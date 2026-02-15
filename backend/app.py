from __future__ import annotations

import os
from typing import Any, Tuple

from flask import Flask, jsonify, request, send_from_directory

from backend.automation_adapter import AutomationAdapter
from backend.clinical_extraction import ClinicalExtractionService
from backend.mock_assistant import MockAssistantService
from backend.phase2_triage import Phase2TriageService
from backend.phase3_vitals import risk_check_local, try_post_phase3
from backend.phase4_cv import try_get_phase4_health
from backend.watson_service import WatsonService


HELP_TEXT = (
    "Tudo bem. Eu posso te ajudar com um atendimento inicial.\n\n"
    "Se você quiser, diga uma destas opções:\n"
    "- \"Quero agendar uma consulta\"\n"
    "- \"Estou com dor no peito\"\n"
    "- \"O que é pressão alta?\"\n\n"
    "O que está acontecendo com você agora?"
)

def _build_assistant() -> Tuple[Any, str]:
    """Cria a implementação do assistente (Watson ou Local)."""
    mode = os.getenv("CARDIOIA_ASSISTANT_MODE", "watson").strip().lower()
    if mode in ["local", "mock"]:
        print("Iniciando em modo LOCAL (offline).")
        return MockAssistantService(), "local"

    try:
        svc = WatsonService()
        print("Conectado ao IBM Watson com sucesso.")
        return svc, "watson"
    except Exception as e:
        # Para avaliação: se não tiver credenciais, ainda permite rodar em modo local.
        print(f"Erro ao conectar com Watson: {e}")
        print("Fazendo fallback para modo LOCAL (offline).")
        return MockAssistantService(), "local"


def create_app() -> Flask:
    # Frontend (React build) fica em `backend/static` (gerado pelo Vite).
    app = Flask(__name__, static_folder="static")
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    assistant, assistant_kind = _build_assistant()
    app.config["assistant"] = assistant
    app.config["assistant_kind"] = assistant_kind
    # Armazenamento simples de sessão em memória (para protótipo).
    # Em produção, usaria Redis ou banco de dados.
    app.config["user_sessions"] = {}

    # Integracoes (fases anteriores + ir alem).
    app.config["phase2_triage"] = Phase2TriageService()
    app.config["clinical_extraction"] = ClinicalExtractionService()
    app.config["automation"] = AutomationAdapter()

    @app.get("/api/status")
    def status():
        cfg_mode = os.getenv("CARDIOIA_ASSISTANT_MODE", "watson").strip().lower()
        assistant = app.config.get("assistant")
        impl = "local" if isinstance(assistant, MockAssistantService) else "watson"

        assistant_id = getattr(assistant, "assistant_id", None)
        environment_id = getattr(assistant, "environment_id", None)

        return jsonify(
            {
                "mode": cfg_mode,
                "assistant": impl,
                "assistant_id": assistant_id,
                "environment_id": environment_id,
            }
        )

    @app.get("/api/config")
    def config():
        # Link opcional para abrir o projeto no IBM Cloud (para o vídeo/avaliação).
        return jsonify(
            {
                "watson_console_url": (os.getenv("WATSON_CONSOLE_URL") or "").strip() or None,
            }
        )

    @app.get("/")
    def home():
        return send_from_directory(app.static_folder, "index.html")

    @app.get("/docs/<path:doc_path>")
    def docs(doc_path: str):
        """
        Serve documentação local para facilitar demonstração e evidência (inclui fases anteriores).

        Rotas suportadas:
        - /docs/fase5/<arquivo> -> document/fase5/<arquivo>
        - /docs/anteriores/<arquivo> -> FASES ANTERIORES/<arquivo>
        - /docs/root/<arquivo> -> arquivos da raiz (ex: CONTRIBUTORS.md)
        """
        doc_path = (doc_path or "").strip().replace("\\", "/")
        if not doc_path:
            return jsonify({"error": "Documento não informado"}), 400

        if doc_path.startswith("fase5/"):
            rel = doc_path.replace("fase5/", "", 1)
            base_dir = os.path.join(repo_root, "document", "fase5")
            return send_from_directory(base_dir, rel)

        if doc_path.startswith("anteriores/"):
            rel = doc_path.replace("anteriores/", "", 1)
            base_dir = os.path.join(repo_root, "FASES ANTERIORES")
            return send_from_directory(base_dir, rel)

        if doc_path.startswith("root/"):
            rel = doc_path.replace("root/", "", 1)
            base_dir = repo_root
            return send_from_directory(base_dir, rel)

        return jsonify({"error": "Prefixo inválido. Use /docs/fase5/…, /docs/anteriores/… ou /docs/root/…"}), 400

    @app.post("/api/message")
    def message():
        data = request.get_json(silent=True) or {}
        user_msg = str(data.get("message") or "")
        user_id = str(data.get("user_id") or "default_user")

        # Conversa "humanizada": mensagem vazia não deve virar erro 400.
        if not user_msg.strip():
            return jsonify({"response": HELP_TEXT, "intents": [], "entities": []})

        assistant = app.config["assistant"]
        user_sessions: dict[str, str] = app.config["user_sessions"]

        # Recupera ou cria sessão para o usuário.
        if user_id not in user_sessions:
            session_id = assistant.create_session()
            if session_id:
                user_sessions[user_id] = session_id
            else:
                # Não explode a conversa com 500: devolve uma resposta orientando o próximo passo.
                return jsonify(
                    {
                        "response": "Eu não consegui iniciar uma sessão agora. Você pode tentar novamente em instantes ou usar o modo local (offline).",
                        "intents": [],
                        "entities": [],
                    }
                )

        session_id = user_sessions[user_id]

        # Envia para o assistente (Watson ou Local).
        # Para Watson, `user_id` pode ser exigido em algumas versões/configurações.
        response_data = assistant.send_message(session_id, user_msg, user_id=user_id)

        # Se a sessão do Watson expirou/inválida, recria e tenta 1 vez.
        if response_data.get("error_type") == "invalid_session":
            new_session_id = assistant.create_session()
            if new_session_id:
                user_sessions[user_id] = new_session_id
                response_data = assistant.send_message(new_session_id, user_msg, user_id=user_id)

        return jsonify(
            {
                "response": response_data.get("text") or "Sem resposta.",
                "intents": response_data.get("intents") or [],
                "entities": response_data.get("entities") or [],
            }
        )

    @app.post("/api/phase2/triage")
    def phase2_triage():
        data = request.get_json(silent=True) or {}
        text = str(data.get("text") or data.get("message") or "")
        if not text.strip():
            return jsonify({"error": "Texto nao informado."}), 400

        svc: Phase2TriageService = app.config["phase2_triage"]
        triage = svc.triage(text.strip())
        return jsonify(
            {
                "risk": triage.risk,
                "diagnosis": triage.diagnosis,
            }
        )

    @app.post("/api/clinical/extract")
    def clinical_extract():
        """
        Ir Alem 1 (GenAI): extrai informacoes clinicas estruturadas a partir de texto livre.
        - Se GEMINI_API_KEY estiver configurada, tenta Gemini.
        - Se nao estiver, faz fallback local + triagem (Fase 2).
        """
        data = request.get_json(silent=True) or {}
        text = str(data.get("text") or data.get("message") or "")
        if not text.strip():
            return jsonify({"error": "Texto nao informado."}), 400

        svc: ClinicalExtractionService = app.config["clinical_extraction"]
        result = svc.extract(text.strip())
        return jsonify(
            {
                "source": result.source,
                "summary": result.summary,
                "structured": result.structured,
                "triage": result.triage,
            }
        )

    @app.get("/api/monitor/logs")
    def monitor_logs():
        """
        Ir Alem 2: leitura dos logs gerados pelo robo (NoSQL em JSON).
        """
        adapter: AutomationAdapter = app.config["automation"]
        return jsonify({"logs": adapter.read_logs()})

    @app.post("/api/monitor/run_once")
    def monitor_run_once():
        """
        Ir Alem 2: roda um ciclo do robo e retorna logs atualizados.
        """
        adapter: AutomationAdapter = app.config["automation"]
        result = adapter.run_once()
        return jsonify({**result, "logs": adapter.read_logs()})

    @app.post("/api/phase3/vitals")
    def phase3_vitals():
        """
        Reuso da Fase 3 (monitoramento continuo):
        - Se PHASE3_ALERTS_URL estiver configurada e o servico estiver rodando, chama o endpoint externo.
        - Caso contrario, aplica a regra local equivalente.
        """
        data = request.get_json(silent=True) or {}
        temp = data.get("temp")
        bpm = data.get("bpm")

        # payload compativel com a Fase 3 (rest_alerts.py)
        payload = {"ts": data.get("ts"), "temp": temp, "hum": data.get("hum"), "bpm": bpm}
        external = try_post_phase3(payload)
        if external is not None:
            return jsonify({"source": "fase3_service", "result": external})

        try:
            temp_f = float(temp) if temp is not None else None
        except Exception:
            temp_f = None
        try:
            bpm_f = float(bpm) if bpm is not None else None
        except Exception:
            bpm_f = None

        return jsonify({"source": "local_rules", "result": risk_check_local(temp_f, bpm_f)})

    @app.get("/api/phase4/health")
    def phase4_health():
        """
        Integracao opcional com a Fase 4 (CV): consulta /health do servico de visao.
        """
        health = try_get_phase4_health()
        return jsonify({"available": health is not None, "health": health})

    return app


if __name__ == "__main__":
    print("Iniciando servidor Flask na porta 5000...")
    app = create_app()
    app.run(debug=True, port=5000)

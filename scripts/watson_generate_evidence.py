"""
Gera evidências "vivas" do Watson (sem segredos):
- environments (list_environments)
- detalhes do environment (get_environment)
- smoke test de conversa (create_session + message)

Uso:
  python scripts/watson_generate_evidence.py

Requer no .env:
  WATSON_API_KEY
  WATSON_URL
  WATSON_ASSISTANT_ID
  WATSON_ENVIRONMENT_ID
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core.api_exception import ApiException
from ibm_watson import AssistantV2


def _load_env() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    candidates = [
        repo_root / ".env",
        repo_root / "FASE5" / ".env",
        Path.cwd() / ".env",
    ]
    for p in candidates:
        if p.exists():
            load_dotenv(p)


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    _load_env()

    api_key = os.getenv("WATSON_API_KEY")
    url = os.getenv("WATSON_URL")
    assistant_id = os.getenv("WATSON_ASSISTANT_ID")
    environment_id = os.getenv("WATSON_ENVIRONMENT_ID")

    if not api_key or not url or not assistant_id or not environment_id:
        print(
            "Faltam variáveis no .env: WATSON_API_KEY, WATSON_URL, WATSON_ASSISTANT_ID, WATSON_ENVIRONMENT_ID.\n"
            "Dica: rode primeiro `python scripts/watson_discover_environment.py`."
        )
        return 2

    authenticator = IAMAuthenticator(api_key)
    wa = AssistantV2(version="2021-06-14", authenticator=authenticator)
    wa.set_service_url(url)

    out_dir = Path(__file__).resolve().parent.parent / "document" / "fase5" / "evidencias"
    _ensure_dir(out_dir)

    # Alguns endpoints administrativos podem falhar em planos lite/contas acadêmicas.
    # Ainda assim, o smoke test (create_session + message) costuma funcionar e é a evidência principal.
    try:
        environments = wa.list_environments(assistant_id=assistant_id).get_result()
    except ApiException as e:
        environments = {"error": str(e)}
    _write_json(out_dir / "watson_environments.json", environments)

    try:
        env_details = wa.get_environment(assistant_id=assistant_id, environment_id=environment_id).get_result()
    except ApiException as e:
        env_details = {"error": str(e)}
    _write_json(out_dir / "watson_environment_details.json", env_details)

    # Smoke test
    session = wa.create_session(assistant_id=assistant_id, environment_id=environment_id).get_result()
    session_id = session.get("session_id")
    if not session_id:
        print("Falha ao criar sessão.")
        return 3

    prompts = [
        "Olá",
        "Quero agendar uma consulta",
        "Estou com dor no peito",
        "Obrigado",
    ]

    results = {
        "assistant_id": assistant_id,
        "environment_id": environment_id,
        "prompts": [],
    }

    for p in prompts:
        r = wa.message(
            assistant_id=assistant_id,
            environment_id=environment_id,
            session_id=session_id,
            user_id="evidencia_fase5",
            input={"message_type": "text", "text": p},
        ).get_result()
        # Salva somente o essencial para evidência.
        out_generic = (r.get("output") or {}).get("generic") or []
        out_text = None
        if out_generic:
            out_text = out_generic[0].get("text")
        results["prompts"].append(
            {
                "input": p,
                "output_text": out_text,
                "intents": (r.get("output") or {}).get("intents") or [],
                "entities": (r.get("output") or {}).get("entities") or [],
            }
        )

    _write_json(out_dir / "watson_smoke_test.json", results)

    print(f"Evidências geradas em: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

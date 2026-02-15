from __future__ import annotations

import json
import os
import re
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


def _strip_accents_lower(s: str) -> str:
    s = (s or "").strip().lower()
    s = "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", s)


def _tokenize(s: str) -> set[str]:
    s = _strip_accents_lower(s)
    s = re.sub(r"[^a-z0-9\s/:-]", " ", s)
    return {t for t in s.split() if t}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))


def _extract_dialog_text(node: dict[str, Any]) -> str | None:
    """
    Export do Watson (modelo clássico) costuma usar `output.generic[*].values[*].text`.
    """
    out = node.get("output") or {}
    generic = out.get("generic") or []
    for item in generic:
        if item.get("response_type") != "text":
            continue
        # formato comum: values=[{text: "..."}]
        values = item.get("values")
        if isinstance(values, list) and values:
            txt = values[0].get("text")
            if isinstance(txt, str) and txt.strip():
                return txt.strip()
        # fallback
        txt = item.get("text")
        if isinstance(txt, str) and txt.strip():
            return txt.strip()
    return None


@dataclass
class _SkillIndex:
    intents: dict[str, list[str]]
    dialogs_by_condition: dict[str, dict[str, Any]]


class MockAssistantService:
    """
    Modo offline para gravação/avaliação.

    Requisito-chave: o chatbot deve "conversar" localmente usando como base
    o export `watson_skill_export.json` (intents/entities/dialog_nodes).
    """

    def __init__(self) -> None:
        self._skill = self._load_skill()
        self._idx = self._index_skill(self._skill)
        self._sessions: dict[str, dict[str, Any]] = {}  # session_id -> context

    @staticmethod
    def _load_skill() -> dict[str, Any]:
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        skill_path = os.path.join(repo_root, "watson_skill_export.json")
        if not os.path.exists(skill_path):
            raise FileNotFoundError("Arquivo watson_skill_export.json não encontrado na raiz do repositório.")
        return json.loads(open(skill_path, "r", encoding="utf-8").read())

    @staticmethod
    def _index_skill(skill: dict[str, Any]) -> _SkillIndex:
        intents: dict[str, list[str]] = {}
        for it in skill.get("intents", []):
            name = it.get("intent")
            if not isinstance(name, str) or not name:
                continue
            ex = []
            for e in it.get("examples", []):
                t = e.get("text")
                if isinstance(t, str) and t.strip():
                    ex.append(t.strip())
            intents[name] = ex

        dialogs_by_condition: dict[str, dict[str, Any]] = {}
        for dn in skill.get("dialog_nodes", []):
            cond = dn.get("conditions")
            if isinstance(cond, str) and cond.strip():
                dialogs_by_condition[cond.strip()] = dn

        return _SkillIndex(intents=intents, dialogs_by_condition=dialogs_by_condition)

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {
            "state": "start",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "history": [],
        }
        return session_id

    @staticmethod
    def _looks_like_date(msg: str) -> bool:
        msg = (msg or "").strip()
        if re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b", msg):
            return True
        if re.search(r"\b(\d{1,2})-(\d{1,2})-(\d{2,4})\b", msg):
            return True
        # palavras comuns de data
        norm = _strip_accents_lower(msg)
        if any(w in norm for w in ["hoje", "amanha", "segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"]):
            return True
        if re.search(r"\bdia\s+\d{1,2}\b", norm):
            return True
        return False

    def _best_intent(self, message: str) -> tuple[str | None, float]:
        msg_tokens = _tokenize(message)
        best_name = None
        best_score = 0.0

        for name, examples in self._idx.intents.items():
            for ex in examples:
                score = _jaccard(msg_tokens, _tokenize(ex))
                if score > best_score:
                    best_name, best_score = name, score

        # reforços por palavras-chave (em saúde isso melhora bastante)
        norm = _strip_accents_lower(message)
        if any(w in norm for w in ["dor no peito", "infarto", "socorro", "aperto no peito"]):
            return "dor_no_peito", 1.0
        if any(w in norm for w in ["agendar", "marcar", "consulta", "cardiologista", "horario"]):
            return "agendar_consulta", max(best_score, 0.9)
        if any(w in norm for w in ["ola", "oi", "bom dia", "boa tarde", "boa noite"]):
            return "saudacao", max(best_score, 0.85)

        return best_name, best_score

    def _dialog_text_for_condition(self, condition: str) -> str | None:
        node = self._idx.dialogs_by_condition.get(condition)
        if not node:
            return None
        return _extract_dialog_text(node)

    def send_message(self, session_id: str, message_text: str, user_id: str | None = None) -> dict[str, Any]:
        ctx = self._sessions.get(session_id)
        if ctx is None:
            session_id = self.create_session()
            ctx = self._sessions[session_id]

        raw = message_text or ""
        norm = _strip_accents_lower(raw)
        state = ctx.get("state", "start")

        is_yes = norm in ["sim", "s", "claro", "isso", "com certeza", "ok", "certo"]
        is_no = norm in ["nao", "não", "n", "negativo"]

        # Estado: aguardando confirmação na emergência
        if state == "emergencia_confirmacao":
            # O export do Watson usa condição `#sim || @sintoma:tontura`.
            # Para manter coerência no modo local, tratamos sintomas de alerta como "sim".
            has_red_flag_symptom = any(w in norm for w in ["tontura", "nausea", "náusea", "suor frio", "mandibula", "mandíbula", "braco esquerdo", "braço esquerdo"])
            if is_yes:
                ctx["state"] = "start"
                txt = self._dialog_text_for_condition("#sim") or "🚨 **AÇÃO IMEDIATA**\n\n1. Pare tudo e sente-se.\n2. Mastigue uma aspirina.\n3. **LIGUE 192 (SAMU).**"
                return {"text": txt, "intents": [{"intent": "sim", "confidence": 1.0}], "entities": []}
            if has_red_flag_symptom:
                ctx["state"] = "start"
                txt = self._dialog_text_for_condition("#sim") or "🚨 **AÇÃO IMEDIATA**\n\n1. Pare tudo e sente-se.\n2. Mastigue uma aspirina.\n3. **LIGUE 192 (SAMU).**"
                return {"text": txt, "intents": [{"intent": "sim", "confidence": 1.0}], "entities": [{"entity": "sintoma", "value": "red_flag"}]}
            if is_no:
                ctx["state"] = "start"
                return {
                    "text": "Mesmo sendo leve, dores no peito devem ser investigadas. Gostaria de agendar uma consulta?",
                    "intents": [{"intent": "nao", "confidence": 1.0}],
                    "entities": [],
                }
            return {
                "text": "Por favor, responda com **Sim** ou **Não** para eu orientar com segurança.",
                "intents": [{"intent": "fallback_confirmacao", "confidence": 1.0}],
                "entities": [],
            }

        # Estado: aguardando data do agendamento
        if state == "agendamento_data":
            if self._looks_like_date(raw):
                ctx["state"] = "start"
                txt = self._dialog_text_for_condition("@sys-date") or f"Entendido. Consulta pré-agendada para **{raw.strip()}**."
                # substitui placeholder usado no export
                txt = txt.replace("<? @sys-date ?>", raw.strip())
                return {
                    "text": txt,
                    "intents": [{"intent": "informar_data", "confidence": 1.0}],
                    "entities": [{"entity": "sys-date", "value": raw.strip()}],
                }
            return {
                "text": "Me diga uma data para eu pré-agendar (ex: `10/03/2026`).",
                "intents": [{"intent": "pedir_data", "confidence": 1.0}],
                "entities": [],
            }

        # Classifica intenção a partir das intents do JSON
        intent, score = self._best_intent(raw)
        ctx.get("history", []).append(
            {"role": "user", "text": raw.strip(), "ts": datetime.now(timezone.utc).isoformat()}
        )

        if intent == "dor_no_peito":
            ctx["state"] = "emergencia_confirmacao"
            txt = self._dialog_text_for_condition("#dor_no_peito")
            if not txt:
                txt = "🔴 **ALERTA DE EMERGÊNCIA** 🔴\n\nA dor irradia para o braço esquerdo ou mandíbula? Você sente náusea ou suor frio?"
            return {"text": txt, "intents": [{"intent": intent, "confidence": score}], "entities": []}

        if intent == "agendar_consulta":
            ctx["state"] = "agendamento_data"
            txt = self._dialog_text_for_condition("#agendar_consulta") or "Certo, vamos agendar. Para qual dia você gostaria de marcar a consulta?"
            return {"text": txt, "intents": [{"intent": intent, "confidence": score}], "entities": []}

        if intent == "falta_de_ar":
            txt = self._dialog_text_for_condition("#falta_de_ar") or (
                "Entendi. Falta de ar pode ter várias causas.\n\n"
                "Você está com dor no peito, tontura ou lábios arroxeados agora?"
            )
            return {"text": txt, "intents": [{"intent": intent, "confidence": score}], "entities": []}

        if intent == "info_pressao":
            txt = self._dialog_text_for_condition("#info_pressao") or (
                "Pressão alta é quando a pressão arterial fica frequentemente elevada.\n\n"
                "Se você tiver uma medida recente (ex: 150/95), pode me dizer?"
            )
            return {"text": txt, "intents": [{"intent": intent, "confidence": score}], "entities": []}

        if intent == "agradecimento":
            txt = self._dialog_text_for_condition("#agradecimento") or "De nada. Como posso te ajudar?"
            return {"text": txt, "intents": [{"intent": intent, "confidence": score}], "entities": []}

        if intent == "saudacao":
            txt = self._dialog_text_for_condition("#saudacao") or "Olá! Como posso ajudar?"
            return {"text": txt, "intents": [{"intent": intent, "confidence": score}], "entities": []}

        # Sim/Não fora de contexto: conversa humanizada precisa pedir esclarecimento.
        if is_yes or is_no:
            return {
                "text": (
                    "Entendi. Só para eu não te orientar errado:\n\n"
                    "1) Você quer **agendar uma consulta**?\n"
                    "ou\n"
                    "2) Você está com **algum sintoma agora** (dor no peito, falta de ar, palpitações)?\n\n"
                    "Me diga qual opção faz mais sentido para você."
                ),
                "intents": [{"intent": "esclarecer_contexto", "confidence": 1.0}],
                "entities": [],
            }

        # Fallback do JSON
        txt = self._dialog_text_for_condition("anything_else") or "Desculpe, não entendi. Tente: \"Quero agendar uma consulta\"."

        # Heurística útil (não substitui o Watson): leitura de pressão no formato 150/95
        m = re.search(r"\b(\d{2,3})\s*/\s*(\d{2,3})\b", raw)
        if m:
            sys = int(m.group(1))
            dia = int(m.group(2))
            if sys >= 180 or dia >= 120:
                return {
                    "text": f"Uma medida de **{sys}/{dia}** pode indicar urgência.\n\nSe você estiver com sintomas (dor no peito, falta de ar, confusão), procure atendimento imediatamente.",
                    "intents": [{"intent": "info_pressao", "confidence": 0.9}],
                    "entities": [{"entity": "pressao", "value": f"{sys}/{dia}"}],
                }
            if sys >= 140 or dia >= 90:
                return {
                    "text": f"Uma medida de **{sys}/{dia}** está acima do ideal.\n\nSe isso for frequente, vale agendar uma avaliação. Você quer pré-agendar uma consulta?",
                    "intents": [{"intent": "info_pressao", "confidence": 0.9}],
                    "entities": [{"entity": "pressao", "value": f"{sys}/{dia}"}],
                }
            return {
                "text": f"**{sys}/{dia}** parece dentro de um intervalo comum.\n\nSe houver sintomas ou dúvidas, posso ajudar a organizar as informações ou pré-agendar uma consulta.",
                "intents": [{"intent": "info_pressao", "confidence": 0.7}],
                "entities": [{"entity": "pressao", "value": f"{sys}/{dia}"}],
            }

        return {"text": txt, "intents": [], "entities": []}

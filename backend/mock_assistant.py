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
    def _arm_side(norm: str) -> str | None:
        if any(w in norm for w in ["esquerdo", "esquerda"]):
            return "esquerdo"
        if any(w in norm for w in ["direito", "direita"]):
            return "direito"
        return None

    @staticmethod
    def _wants_doctor(norm: str) -> bool:
        # "onde acho um medico", "quero um medico", "hospital", etc.
        return any(
            w in norm
            for w in [
                "onde acho",
                "onde eu acho",
                "onde encontro",
                "um medico",
                "um médico",
                "medico",
                "médico",
                "hospital",
                "pronto socorro",
                "pronto atendimento",
                "consulta",
                "agendar",
                "marcar",
            ]
        )

    @staticmethod
    def _is_cancel(norm: str) -> bool:
        return any(w in norm for w in ["cancelar", "cancela", "sair", "parar", "para", "pare", "deixa pra la", "deixa pra lá"])

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

        # Evita falso-positivo: se a similaridade for muito baixa, trate como "sem intenção".
        if best_score < 0.34:
            best_name = None

        # reforços por palavras-chave (em saúde isso melhora bastante)
        norm = _strip_accents_lower(message)
        # Negacao explicita evita falso positivo para dor no peito.
        if ("nao" in norm or "não" in norm) and "peito" in norm and "dor" not in norm:
            return None, 0.0
        if any(w in norm for w in ["dor no peito", "infarto", "socorro", "aperto no peito"]):
            return "dor_no_peito", 1.0
        if any(w in norm for w in ["agendar", "marcar", "consulta", "cardiologista", "horario"]):
            return "agendar_consulta", max(best_score, 0.9)
        if any(w in norm for w in ["ola", "oi", "bom dia", "boa tarde", "boa noite"]):
            return "saudacao", max(best_score, 0.85)

        # Guard rail importante: não trate "dor no braço" como "dor no peito" só por similaridade.
        # Isso evita o falso-positivo mais comum no modo LOCAL (Jaccard com exemplos do Watson).
        if best_name == "dor_no_peito" and not any(w in norm for w in ["peito", "torax", "tórax", "aperto no peito"]):
            best_name = None
            best_score = 0.0

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

        is_yes = norm in ["sim", "s", "claro", "isso", "com certeza", "ok", "certo", "aham", "uhum", "sinto", "tenho"]
        is_no = norm in ["nao", "não", "n", "negativo", "nao tenho", "não tenho"]

        # Cancelamento global (não deve prender usuário em nenhum fluxo).
        if self._is_cancel(norm):
            ctx["state"] = "start"
            return {
                "text": "Tudo bem. Como você prefere seguir agora: agendar uma consulta ou descrever um sintoma (dor no peito, falta de ar, palpitações)?",
                "intents": [{"intent": "cancelar", "confidence": 1.0}],
                "entities": [],
            }

        # Atalho "humano" para entradas muito vagas.
        if state == "start" and any(w in norm for w in ["to ruim", "tô ruim", "to mal", "tô mal", "passando mal", "mal"]):
            return {
                "text": (
                    "Entendi. Para eu te ajudar sem adivinhar:\n\n"
                    "1) Qual é o sintoma principal agora? (ex.: dor no peito, falta de ar, palpitações, tontura)\n"
                    "2) Isso começou há quanto tempo?\n\n"
                    "Se preferir, você também pode dizer: \"quero agendar uma consulta\"."
                ),
                "intents": [{"intent": "sintoma_vago", "confidence": 1.0}],
                "entities": [],
            }

        # Estado: emergência (pergunta 1) - irradiação
        if state in ["emergencia_confirmacao", "emergencia_irradia"]:
            # Compat: estados antigos caem aqui (emergencia_confirmacao).
            ctx["state"] = "emergencia_irradia"

            # Se o usuário tentar "sair" perguntando por médico, não trave o fluxo.
            if self._wants_doctor(norm):
                ctx["state"] = "agendamento_data"
                return {
                    "text": "Posso pré-agendar uma consulta por aqui. Para qual dia você gostaria de marcar? (Ex: 10/03/2026, amanhã, segunda que vem)",
                    "intents": [{"intent": "agendar_consulta", "confidence": 1.0}],
                    "entities": [],
                }

            # Aceita "no direito/no esquerdo" como resposta válida para a pergunta de irradiação ao braço esquerdo.
            arm_side = self._arm_side(norm)
            if arm_side == "direito":
                is_no = True
            if arm_side == "esquerdo":
                is_yes = True

            mentions_jaw = any(w in norm for w in ["mandibula", "mandíbula"])
            if mentions_jaw:
                is_yes = True

            if is_yes:
                ctx["emergency_irradia"] = True
                ctx["state"] = "emergencia_sintomas"
                return {
                    "text": "Obrigado. Agora responda **Sim** ou **Não**: você sente falta de ar, náusea ou suor frio agora?",
                    "intents": [{"intent": "emergencia_irradia_sim", "confidence": 1.0}],
                    "entities": [],
                }
            if is_no:
                ctx["emergency_irradia"] = False
                ctx["state"] = "emergencia_sintomas"
                return {
                    "text": "Entendi. Agora responda **Sim** ou **Não**: você sente falta de ar, náusea ou suor frio agora?",
                    "intents": [{"intent": "emergencia_irradia_nao", "confidence": 1.0}],
                    "entities": [],
                }

            # Se a pessoa está confusa ("sim ou não o quê?"), deixa explícito qual pergunta está ativa.
            if any(w in norm for w in ["sim ou nao", "sim ou não", "o que", "oq", "do que"]):
                return {
                    "text": "Só para eu seguir a triagem: **a dor/pressão se espalha para o braço esquerdo ou para a mandíbula?** (Sim/Não)",
                    "intents": [{"intent": "emergencia_clarificar", "confidence": 1.0}],
                    "entities": [],
                }

            # Escape hatch: não fica preso pedindo Sim/Não para sempre.
            ctx["emergency_attempts"] = int(ctx.get("emergency_attempts") or 0) + 1
            if ctx["emergency_attempts"] >= 2:
                ctx["state"] = "start"
                return {
                    "text": (
                        "Tudo bem. Eu não quero te prender em perguntas.\n\n"
                        "Você prefere:\n"
                        "- agendar uma consulta, ou\n"
                        "- descrever rapidamente o que está sentindo (ex.: dor no peito, falta de ar, palpitações)?"
                    ),
                    "intents": [{"intent": "emergencia_escape", "confidence": 1.0}],
                    "entities": [],
                }

            return {
                "text": "Responda com **Sim** ou **Não**: a dor/pressão se espalha para o braço esquerdo ou para a mandíbula?",
                "intents": [{"intent": "emergencia_irradia_reprompt", "confidence": 1.0}],
                "entities": [],
            }

        # Estado: emergência (pergunta 2) - sintomas associados
        if state == "emergencia_sintomas":
            if self._wants_doctor(norm):
                ctx["state"] = "agendamento_data"
                return {
                    "text": "Posso pré-agendar uma consulta por aqui. Para qual dia você gostaria de marcar? (Ex: 10/03/2026, amanhã, segunda que vem)",
                    "intents": [{"intent": "agendar_consulta", "confidence": 1.0}],
                    "entities": [],
                }

            if is_yes or any(w in norm for w in ["falta de ar", "suor frio", "nausea", "náusea", "tontura", "desmaio"]):
                ctx["state"] = "start"
                return {
                    "text": (
                        "Sinais de alerta identificados.\n\n"
                        "Procure **atendimento de emergência imediatamente**.\n\n"
                        "Se você quiser, depois disso eu posso ajudar a pré-agendar um retorno com cardiologista."
                    ),
                    "intents": [{"intent": "emergencia_alta", "confidence": 1.0}],
                    "entities": [{"entity": "risk", "value": "alto"}],
                }

            if is_no:
                ctx["state"] = "agendamento_data"
                return {
                    "text": (
                        "Entendi. Mesmo sem outros sinais agora, dor no peito merece avaliação.\n\n"
                        "Quer pré-agendar uma consulta? Para qual dia você gostaria de marcar?"
                    ),
                    "intents": [{"intent": "emergencia_media", "confidence": 1.0}],
                    "entities": [{"entity": "risk", "value": "moderado"}],
                }

            if any(w in norm for w in ["sim ou nao", "sim ou não", "o que", "oq", "do que"]):
                return {
                    "text": "Só para eu seguir: **você sente falta de ar, náusea ou suor frio agora?** (Sim/Não)",
                    "intents": [{"intent": "emergencia_clarificar_2", "confidence": 1.0}],
                    "entities": [],
                }

            ctx["emergency_attempts_2"] = int(ctx.get("emergency_attempts_2") or 0) + 1
            if ctx["emergency_attempts_2"] >= 2:
                ctx["state"] = "start"
                return {
                    "text": "Tudo bem. Quer que eu pré-agende uma consulta ou prefere descrever o sintoma principal com outras palavras?",
                    "intents": [{"intent": "emergencia_escape_2", "confidence": 1.0}],
                    "entities": [],
                }

            return {
                "text": "Responda com **Sim** ou **Não**: você sente falta de ar, náusea ou suor frio agora?",
                "intents": [{"intent": "emergencia_sintomas_reprompt", "confidence": 1.0}],
                "entities": [],
            }

        # Estado: aguardando data do agendamento
        if state == "agendamento_data":
            if self._looks_like_date(raw):
                # Depois da data, pedimos uma observacao/motivo (estado dedicado) para nao entrar em loop.
                ctx["state"] = "agendamento_observacao"
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

        # Estado: coletando observacao/motivo do agendamento
        if state == "agendamento_observacao":
            ctx["state"] = "start"
            motivo = raw.strip()
            if not motivo:
                return {
                    "text": "Tudo bem. Consulta pré-agendada. Posso te ajudar com mais alguma coisa?",
                    "intents": [{"intent": "confirmar_agendamento", "confidence": 1.0}],
                    "entities": [],
                }
            # Se o usuario mandar outra data aqui, trate como observacao mesmo (nao reinicia fluxo).
            return {
                "text": f"Perfeito. Registrei a observação: **{motivo}**.\n\nPosso te ajudar com mais alguma coisa?",
                "intents": [{"intent": "confirmar_agendamento", "confidence": 1.0}],
                "entities": [{"entity": "observacao", "value": motivo}],
            }

        # Estado: esclarecendo localizacao/descricao de dor (antes de assumir dor no peito)
        if state == "dor_esclarecimento":
            # Se o usuario negar explicitamente "peito", NAO dispare emergencia.
            if ("nao" in norm or "não" in norm) and "peito" in norm:
                ctx["state"] = "start"
                return {
                    "text": (
                        "Entendi, então **não é dor no peito**.\n\n"
                        "Para eu não te orientar errado, me diga onde é a dor (ex.: barriga, costas, cabeça, dente...) "
                        "e se você tem algum sintoma como falta de ar, palpitações, tontura, náusea ou suor frio."
                    ),
                    "intents": [{"intent": "esclarecer_dor", "confidence": 1.0}],
                    "entities": [{"entity": "dor_no_peito", "value": "nao"}],
                }

            # Se mencionar peito sem negacao, ai sim segue o fluxo de emergencia.
            if "peito" in norm:
                ctx["state"] = "emergencia_irradia"
                # No modo LOCAL, preferimos uma pergunta binária (uma coisa por vez),
                # em vez de reutilizar o texto do export (que costuma juntar 2 perguntas).
                return {
                    "text": "Responda **Sim** ou **Não**: a dor/pressão se espalha para o braço esquerdo ou para a mandíbula?",
                    "intents": [{"intent": "dor_no_peito", "confidence": 0.9}],
                    "entities": [],
                }

            # Palavras de localizacao fora do escopo cardiologico: faz redirecionamento.
            if any(w in norm for w in ["dente", "dent", "rabiga", "bunda", "anus", "ânus"]):
                ctx["state"] = "start"
                return {
                    "text": (
                        "Entendi. Isso parece fugir do meu foco (cardiologia).\n\n"
                        "Se você quiser, eu posso ajudar a **organizar** o que você está sentindo (para levar a uma consulta) "
                        "ou, se houver sintomas cardíacos, seguir com uma triagem por aqui.\n\n"
                        "Você prefere organizar as informações ou falar de sintomas como dor no peito, falta de ar ou palpitações?"
                    ),
                    "intents": [{"intent": "fora_escopo", "confidence": 1.0}],
                    "entities": [],
                }

            # Se nao deu para entender, continua perguntando.
            return {
                "text": (
                    "Entendi. Só para eu acertar:\n\n"
                    "Onde exatamente é a dor (peito, costas, barriga, cabeça, dente...)?"
                ),
                "intents": [{"intent": "esclarecer_dor", "confidence": 1.0}],
                "entities": [],
            }

        # Classifica intenção a partir das intents do JSON
        intent, score = self._best_intent(raw)
        ctx.get("history", []).append(
            {"role": "user", "text": raw.strip(), "ts": datetime.now(timezone.utc).isoformat()}
        )

        # Dor no braço (muito comum em conversa humana): não dispare emergência direto.
        if "dor" in norm and any(w in norm for w in ["braco", "braço"]) and "peito" not in norm and state == "start":
            ctx["state"] = "braco_lado"
            return {
                "text": "Entendi: dor no braço. É no braço **esquerdo** ou **direito**?",
                "intents": [{"intent": "dor_no_braco", "confidence": 1.0}],
                "entities": [],
            }

        # Fluxo: dor no braço -> coletar lado
        if state == "braco_lado":
            side = self._arm_side(norm)
            if side:
                ctx["arm_side"] = side
                ctx["state"] = "braco_peito"
                return {
                    "text": "Obrigado. Agora responda **Sim** ou **Não**: você também sente dor/pressão no **peito**?",
                    "intents": [{"intent": "braco_lado_informado", "confidence": 1.0}],
                    "entities": [{"entity": "arm_side", "value": side}],
                }
            return {
                "text": "Só para eu registrar: é no braço **esquerdo** ou **direito**?",
                "intents": [{"intent": "braco_lado_perguntar", "confidence": 1.0}],
                "entities": [],
            }

        # Fluxo: dor no braço -> pergunta se há dor no peito
        if state == "braco_peito":
            if self._wants_doctor(norm):
                ctx["state"] = "agendamento_data"
                return {
                    "text": "Posso pré-agendar uma consulta por aqui. Para qual dia você gostaria de marcar?",
                    "intents": [{"intent": "agendar_consulta", "confidence": 1.0}],
                    "entities": [],
                }
            if is_yes or "peito" in norm:
                ctx["state"] = "emergencia_irradia"
                return {
                    "text": "Entendi. Responda **Sim** ou **Não**: a dor/pressão se espalha para o braço esquerdo ou para a mandíbula?",
                    "intents": [{"intent": "dor_no_peito", "confidence": 1.0}],
                    "entities": [],
                }
            if is_no:
                ctx["state"] = "braco_sintomas"
                return {
                    "text": "Entendi. Responda **Sim** ou **Não**: você tem falta de ar, tontura, náusea ou suor frio junto dessa dor?",
                    "intents": [{"intent": "braco_sem_peito", "confidence": 1.0}],
                    "entities": [],
                }
            # Evita travar o usuario: explica a pergunta e oferece saida.
            if any(w in norm for w in ["sim ou nao", "sim ou não", "o que", "oq", "do que", "como assim"]):
                return {
                    "text": "Só para eu entender o risco: **além do braço, você sente dor/pressão no peito?** (Sim/Não)",
                    "intents": [{"intent": "braco_peito_clarificar", "confidence": 1.0}],
                    "entities": [],
                }

            ctx["braco_attempts"] = int(ctx.get("braco_attempts") or 0) + 1
            if ctx["braco_attempts"] >= 2:
                ctx["state"] = "start"
                return {
                    "text": (
                        "Tudo bem. Sem essa resposta eu não quero te orientar errado.\n\n"
                        "Você prefere:\n"
                        "- pré-agendar uma consulta, ou\n"
                        "- descrever a dor em 1 frase (ex.: pontada, formigamento, começou quando)?"
                    ),
                    "intents": [{"intent": "braco_escape", "confidence": 1.0}],
                    "entities": [],
                }

            return {
                "text": "Para eu seguir: além do braço, você sente dor/pressão no **peito**? (Sim/Não)",
                "intents": [{"intent": "braco_peito_reprompt", "confidence": 1.0}],
                "entities": [],
            }

        # Fluxo: dor no braço -> sintomas associados
        if state == "braco_sintomas":
            if self._wants_doctor(norm):
                ctx["state"] = "agendamento_data"
                return {
                    "text": "Posso pré-agendar uma consulta por aqui. Para qual dia você gostaria de marcar?",
                    "intents": [{"intent": "agendar_consulta", "confidence": 1.0}],
                    "entities": [],
                }
            if is_yes or any(w in norm for w in ["falta de ar", "tontura", "nausea", "náusea", "suor frio", "desmaio"]):
                ctx["state"] = "start"
                return {
                    "text": "Entendi. Esses sinais podem indicar maior risco. Procure avaliação médica com urgência. Se quiser, posso pré-agendar uma consulta.",
                    "intents": [{"intent": "braco_alerta", "confidence": 1.0}],
                    "entities": [{"entity": "risk", "value": "moderado"}],
                }
            if is_no:
                ctx["state"] = "agendamento_data"
                return {
                    "text": "Entendi. Posso pré-agendar uma consulta para você investigar isso com calma. Para qual dia você gostaria de marcar?",
                    "intents": [{"intent": "agendar_consulta", "confidence": 1.0}],
                    "entities": [],
                }
            return {
                "text": "Responda com **Sim** ou **Não**: você tem falta de ar, tontura, náusea ou suor frio junto dessa dor?",
                "intents": [{"intent": "braco_sintomas_reprompt", "confidence": 1.0}],
                "entities": [],
            }

        # Dor fora do contexto cardiologico: pede esclarecimento antes de disparar emergencia.
        if "dor" in norm and intent is None:
            ctx["state"] = "dor_esclarecimento"
            return {
                "text": (
                    "Entendi que você está com dor.\n\n"
                    "Para eu te orientar melhor, me diga:\n"
                    "1) Onde é a dor (peito, costas, barriga, cabeça, dente...)?\n"
                    "2) Começou quando?\n"
                    "3) Tem falta de ar, tontura, náusea ou suor frio junto?"
                ),
                "intents": [{"intent": "esclarecer_dor", "confidence": 1.0}],
                "entities": [],
            }

        # Sintomas claramente fora do escopo cardiologico: faz redirecionamento sem travar fluxo.
        if any(w in norm for w in ["dente", "dent", "rabiga", "bunda", "anus", "ânus"]) and intent != "dor_no_peito":
            return {
                "text": (
                    "Entendi. Isso parece fugir do meu foco (cardiologia).\n\n"
                    "Se você quiser, eu posso:\n"
                    "- ajudar a **organizar** as informações (para levar a uma consulta)\n"
                    "- ou **pré-agendar** uma consulta com cardiologista, se houver sintomas cardíacos.\n\n"
                    "Você quer organizar as informações ou falar de sintomas como dor no peito, falta de ar ou palpitações?"
                ),
                "intents": [{"intent": "fora_escopo", "confidence": 1.0}],
                "entities": [],
            }

        if intent == "dor_no_peito":
            ctx["state"] = "emergencia_irradia"
            return {
                "text": "Responda **Sim** ou **Não**: a dor/pressão se espalha para o braço esquerdo ou para a mandíbula?",
                "intents": [{"intent": intent, "confidence": score}],
                "entities": [],
            }

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

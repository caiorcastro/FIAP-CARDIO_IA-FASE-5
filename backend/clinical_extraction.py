from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Optional

from backend.phase2_triage import Phase2TriageService


def _extract_json_blob(text: str) -> str | None:
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start : end + 1]


def _try_parse_json(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        blob = _extract_json_blob(text)
        if not blob:
            return None
        try:
            return json.loads(blob)
        except Exception:
            return None


def _extract_vitals_simple(text: str) -> dict[str, Any]:
    """
    Extracao simples via regex (sem LLM):
    - PA: 150/95
    - FC: 88bpm, 88 bpm, fc 88
    - Temp: 38.2, 38,2, 38 C
    """
    t = (text or "")

    vitals: dict[str, Any] = {}

    m = re.search(r"\b(\d{2,3})\s*/\s*(\d{2,3})\b", t)
    if m:
        vitals["pressao_arterial"] = f"{m.group(1)}/{m.group(2)}"

    m = re.search(r"\b(?:fc|frequencia cardiaca|bpm)\s*[:=]?\s*(\d{2,3})\b", t, re.I)
    if m:
        vitals["frequencia_cardiaca_bpm"] = int(m.group(1))
    else:
        m = re.search(r"\b(\d{2,3})\s*bpm\b", t, re.I)
        if m:
            vitals["frequencia_cardiaca_bpm"] = int(m.group(1))

    m = re.search(r"\b(?:temp|temperatura)\s*[:=]?\s*(\d{2})(?:[\\.,](\d))?\s*(?:c|°c)?\b", t, re.I)
    if m:
        dec = m.group(2) or "0"
        vitals["temperatura_c"] = float(f"{m.group(1)}.{dec}")

    return vitals


@dataclass(frozen=True)
class ClinicalExtractionResult:
    source: str  # "gemini" | "local"
    summary: str
    structured: dict[str, Any]
    triage: dict[str, Any]


class GeminiClinicalExtractor:
    def __init__(self) -> None:
        self._api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
        self._model_name = (os.getenv("GEMINI_MODEL") or "").strip()
        self._model = None

        if not self._api_key:
            return

        import google.generativeai as genai  # local import para nao forcar em cenarios sem uso

        genai.configure(api_key=self._api_key)

        candidates = [self._model_name] if self._model_name else []
        # Ordem: nomes mais comuns recentes primeiro; fallback para o nome usado no notebook.
        candidates += ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
        candidates = [c for c in candidates if c]

        last_exc: Exception | None = None
        for name in candidates:
            try:
                self._model = genai.GenerativeModel(name)
                self._model_name = name
                last_exc = None
                break
            except Exception as e:
                last_exc = e
                continue

        if self._model is None and last_exc is not None:
            # Deixa para o caller cair no fallback local.
            pass

    def available(self) -> bool:
        return self._model is not None

    def extract(self, user_text: str) -> tuple[dict[str, Any] | None, str | None]:
        if not self._model:
            return None, None

        prompt = (
            "Voce e' um assistente clinico. Extraia informacoes do texto do paciente e devolva APENAS JSON valido.\n\n"
            "Regras:\n"
            "- Responda somente com JSON (sem markdown, sem texto antes/depois).\n"
            "- Se algum campo nao existir no texto, use null.\n"
            "- Campos:\n"
            "  queixa_principal: string|null\n"
            "  sintomas: array<string>\n"
            "  duracao: string|null\n"
            "  sinais_vitais: {pressao_arterial:string|null, frequencia_cardiaca_bpm:number|null, temperatura_c:number|null}\n"
            "  historico: array<string>\n"
            "  medicamentos: array<string>\n"
            "  alergias: array<string>\n"
            "  red_flags: array<string>\n"
            "  perguntas_de_seguimento: array<string>\n\n"
            f"Texto do paciente:\n{user_text.strip()}\n"
        )

        try:
            resp = self._model.generate_content(prompt)
            txt = (getattr(resp, "text", None) or "").strip()
            data = _try_parse_json(txt)
            return data, txt
        except Exception:
            return None, None


class ClinicalExtractionService:
    def __init__(self) -> None:
        self._triage = Phase2TriageService()
        self._gemini = GeminiClinicalExtractor()

    def extract(self, text: str) -> ClinicalExtractionResult:
        raw = (text or "").strip()
        triage = self._triage.triage(raw)
        triage_payload = {"risk": triage.risk, "diagnosis": triage.diagnosis}

        if self._gemini.available() and raw:
            structured, _raw_txt = self._gemini.extract(raw)
            if structured is not None:
                summary = self._build_summary(structured, triage_payload)
                return ClinicalExtractionResult(
                    source="gemini",
                    summary=summary,
                    structured=structured,
                    triage=triage_payload,
                )

        # Fallback local: regex + triagem (Fase 2)
        vitals = _extract_vitals_simple(raw)
        structured = {
            "queixa_principal": None,
            "sintomas": [],
            "duracao": None,
            "sinais_vitais": {
                "pressao_arterial": vitals.get("pressao_arterial"),
                "frequencia_cardiaca_bpm": vitals.get("frequencia_cardiaca_bpm"),
                "temperatura_c": vitals.get("temperatura_c"),
            },
            "historico": [],
            "medicamentos": [],
            "alergias": [],
            "red_flags": [],
            "perguntas_de_seguimento": [
                "Ha quanto tempo isso comecou?",
                "A dor irradia para braco, mandibula ou costas?",
                "Voce teve falta de ar, tontura, nausea ou suor frio?",
                "Voce mediu pressao ou frequencia cardiaca recentemente?",
            ],
        }
        summary = self._build_summary(structured, triage_payload)
        return ClinicalExtractionResult(source="local", summary=summary, structured=structured, triage=triage_payload)

    @staticmethod
    def _build_summary(structured: dict[str, Any], triage: dict[str, Any]) -> str:
        vit = structured.get("sinais_vitais") or {}
        bp = vit.get("pressao_arterial")
        hr = vit.get("frequencia_cardiaca_bpm")
        temp = vit.get("temperatura_c")
        parts = []
        if bp or hr or temp:
            parts.append(
                "Sinais vitais citados: "
                + ", ".join([p for p in [f"PA {bp}" if bp else None, f"FC {hr} bpm" if hr else None, f"Temp {temp} C" if temp else None] if p])
                + "."
            )

        risk = (triage.get("risk") or "").strip()
        if risk:
            parts.append(f"Triagem (Fase 2): {risk}.")

        disease = ((triage.get("diagnosis") or {}).get("disease") or "").strip()
        conf = (triage.get("diagnosis") or {}).get("confidence")
        if disease:
            parts.append(f"Diagnostico sugerido (Fase 2): {disease} (confianca {conf}).")

        return " ".join(parts).strip() or "Extracao concluida."

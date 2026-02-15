from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Phase2Triage:
    risk: str
    diagnosis: dict[str, Any]


class Phase2TriageService:
    """
    Integra a Fase 2 (NLP/triagem) na Fase 5.

    A ideia aqui e' reaproveitar o codigo que ja existe em:
    `FASES ANTERIORES/Fase2/src/diagnose.py`.
    """

    def __init__(self) -> None:
        self._repo_root = Path(__file__).resolve().parents[1]
        self._phase2_dir = self._repo_root / "FASES ANTERIORES" / "Fase2"
        self._mod = self._load_phase2_module()
        self._rules = self._load_rules()

    def _load_phase2_module(self):
        diagnose_path = self._phase2_dir / "src" / "diagnose.py"
        if not diagnose_path.exists():
            return None

        spec = importlib.util.spec_from_file_location("cardioia_phase2_diagnose", str(diagnose_path))
        if spec is None or spec.loader is None:
            return None

        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[attr-defined]
        return mod

    def _load_rules(self):
        if self._mod is None:
            return None

        km = self._phase2_dir / "data" / "knowledge_map.csv"
        if not km.exists():
            return None

        try:
            return self._mod.load_knowledge_map(km)
        except Exception:
            return None

    def triage(self, text: str) -> Phase2Triage:
        text = (text or "").strip()
        if not text:
            return Phase2Triage(risk="indefinido", diagnosis={"disease": "Indefinido", "matched": [], "confidence": 0.0})

        if self._mod is None:
            # Fallback minimo (nao depende da Fase 2 estar presente).
            return Phase2Triage(
                risk="indefinido",
                diagnosis={"disease": "Indefinido", "matched": [], "confidence": 0.0},
            )

        try:
            risk = str(self._mod.heuristic_risk(text))
        except Exception:
            risk = "indefinido"

        diagnosis: dict[str, Any] = {"disease": "Indefinido", "matched": [], "confidence": 0.0}
        if self._rules is not None:
            try:
                diagnosis = dict(self._mod.suggest_diagnosis(text, self._rules))
            except Exception:
                diagnosis = {"disease": "Indefinido", "matched": [], "confidence": 0.0}

        return Phase2Triage(risk=risk, diagnosis=diagnosis)


from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


def risk_check_local(temp: float | None, bpm: float | None) -> dict[str, Any]:
    """
    Regra simples reaproveitada da Fase 3 (`FASES ANTERIORES/FASE3/ir-alem/rest_alerts.py`):
    - bpm > 120 => Taquicardia
    - temp > 38 => Febre
    """
    alerts: list[str] = []
    if bpm is not None and bpm > 120:
        alerts.append("Taquicardia")
    if temp is not None and temp > 38:
        alerts.append("Febre")
    risk = "alto" if alerts else "baixo"
    return {"risk": risk, "alerts": alerts}


def try_post_phase3(vitals_payload: dict[str, Any]) -> dict[str, Any] | None:
    """
    Se `PHASE3_ALERTS_URL` estiver configurada, tenta chamar o servico da Fase 3.
    Espera um endpoint compativel com `POST /vitals`.
    """
    url = (os.getenv("PHASE3_ALERTS_URL") or "").strip()
    if not url:
        return None

    data = json.dumps(vitals_payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return json.loads(body)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def try_get_phase4_health() -> dict[str, Any] | None:
    base = (os.getenv("PHASE4_CV_URL") or "").strip()
    if not base:
        return None

    url = base.rstrip("/") + "/health"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return json.loads(body)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


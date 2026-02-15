from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


class AutomationAdapter:
    """
    Integra o "Ir Alem 2" (RPA + dados hibridos) ao backend da Fase 5.
    - SQLite: automation/data/patients.db
    - Logs JSON (NoSQL): automation/data/logs.json
    """

    def __init__(self) -> None:
        self._repo_root = Path(__file__).resolve().parents[1]
        self._automation_dir = self._repo_root / "automation"

        self._db_setup = self._load_module(self._automation_dir / "database_setup.py", "cardioia_db_setup")
        self._rpa = self._load_module(self._automation_dir / "rpa_monitor.py", "cardioia_rpa_monitor")

        self.db_path = self._automation_dir / "data" / "patients.db"
        self.log_path = self._automation_dir / "data" / "logs.json"

    @staticmethod
    def _load_module(path: Path, name: str):
        if not path.exists():
            return None
        spec = importlib.util.spec_from_file_location(name, str(path))
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[attr-defined]
        return mod

    def ensure_db(self) -> bool:
        if self.db_path.exists():
            return True
        if self._db_setup is None:
            return False
        try:
            self._db_setup.create_database()
            return self.db_path.exists()
        except Exception:
            return False

    def run_once(self) -> dict[str, Any]:
        """
        Roda um ciclo do robo e retorna um resumo (nao retorna logs inteiros).
        """
        ok = self.ensure_db()
        if not ok:
            return {"ok": False, "error": "Banco SQLite nao encontrado e nao foi possivel criar automaticamente."}
        if self._rpa is None:
            return {"ok": False, "error": "Modulo de automacao (rpa_monitor.py) nao encontrado."}
        try:
            self._rpa.run_rpa_cycle()
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def read_logs(self) -> list[dict[str, Any]]:
        if not self.log_path.exists():
            return []
        try:
            import json

            return json.loads(self.log_path.read_text(encoding="utf-8"))
        except Exception:
            return []


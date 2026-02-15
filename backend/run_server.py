from __future__ import annotations

# Conveniência: permite rodar `python run_server.py` dentro de `backend/`.
# O entrypoint real vive na raiz em `run_server.py`.

import sys
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))
    from run_server import main as root_main

    root_main()


if __name__ == "__main__":
    main()


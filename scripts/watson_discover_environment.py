"""
Descobre o Environment ID do Watson Assistant (especialmente o ambiente "live").

Uso:
  python scripts/watson_discover_environment.py

Requer no .env:
  WATSON_API_KEY
  WATSON_URL
  WATSON_ASSISTANT_ID  (ou ASSISTANT_ID)
"""

from __future__ import annotations

import json
import os
from pathlib import Path

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


def main() -> int:
    _load_env()

    api_key = os.getenv("WATSON_API_KEY")
    url = os.getenv("WATSON_URL")
    assistant_id = os.getenv("WATSON_ASSISTANT_ID") or os.getenv("ASSISTANT_ID")

    if not api_key or not url or not assistant_id:
        print("Faltam variáveis no .env: WATSON_API_KEY, WATSON_URL, WATSON_ASSISTANT_ID (ou ASSISTANT_ID).")
        return 2

    authenticator = IAMAuthenticator(api_key)
    wa = AssistantV2(version="2021-06-14", authenticator=authenticator)
    wa.set_service_url(url)

    envs = {"environments": [], "note": None}
    try:
        envs = wa.list_environments(assistant_id=assistant_id).get_result()
        items = envs.get("environments", [])

        # Saída legível para copiar/colar no .env
        print("\nEnvironments encontrados:\n")
        for e in items:
            print(f"- name={e.get('name')}  environment_id={e.get('environment_id')}")

        live = next((e for e in items if str(e.get("name", "")).strip().lower() == "live"), None)
        if live:
            print("\nSugestão de .env (à prova de banca):\n")
            print(f"WATSON_ASSISTANT_ID={assistant_id}")
            print(f"WATSON_ENVIRONMENT_ID={live.get('environment_id')}")
        else:
            print("\nObs: não encontrei um environment com name=live. Use o environment_id listado acima.")

    except ApiException as e:
        # Alguns planos/contas retornam 404/400 para endpoints administrativos.
        # Como fallback, testamos o caso mais comum observado em sala: usar o mesmo GUID (assistant_id) como environment_id.
        envs = {"environments": [], "note": f"list_environments falhou: {str(e)}"}

        print("\nNão foi possível listar environments via API (provável limitação do plano/conta).")
        print("Vou testar automaticamente se o próprio ASSISTANT_ID funciona como WATSON_ENVIRONMENT_ID...\n")

        try:
            sess = wa.create_session(assistant_id=assistant_id, environment_id=assistant_id).get_result()
            ok = bool(sess.get("session_id"))
        except Exception as e2:
            ok = False
            envs["note"] += f" | create_session fallback falhou: {str(e2)}"

        if ok:
            print("Teste OK: create_session funcionou usando environment_id = assistant_id.\n")
            print("Sugestão de .env (à prova de banca):\n")
            print(f"WATSON_ASSISTANT_ID={assistant_id}")
            print(f"WATSON_ENVIRONMENT_ID={assistant_id}")
        else:
            print("Teste falhou: não consegui confirmar um environment_id automaticamente.")
            print("Nesse caso, pegue o Environment ID pelo console do Watson (Publish/Environments).")

    # Também salva evidência sem segredos (ou nota de erro).
    out_dir = Path(__file__).resolve().parent.parent / "document" / "fase5" / "evidencias"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "watson_environments.json"
    out_path.write_text(json.dumps(envs, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nEvidência salva em: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

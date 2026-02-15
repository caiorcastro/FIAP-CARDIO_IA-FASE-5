from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _post_json(client, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    res = client.post(path, json=payload)
    try:
        data = res.get_json() or {}
    except Exception:
        data = {"_raw": (res.data or b"").decode("utf-8", errors="replace")}
    return {"status_code": res.status_code, "json": data}


def _get_json(client, path: str) -> dict[str, Any]:
    res = client.get(path)
    try:
        data = res.get_json() or {}
    except Exception:
        data = {"_raw": (res.data or b"").decode("utf-8", errors="replace")}
    return {"status_code": res.status_code, "json": data}


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))
    evid_dir = repo_root / "document" / "fase5" / "evidencias"
    evid_dir.mkdir(parents=True, exist_ok=True)

    # Forca modo LOCAL para o smoke.
    os.environ["CARDIOIA_ASSISTANT_MODE"] = "local"
    # Smoke deve ser estavel/reprodutivel: desativa Gemini mesmo se existir chave no .env.
    os.environ["GEMINI_API_KEY"] = ""
    os.environ["GEMINI_MODEL"] = ""

    # Limpa artefatos de execucao do Ir Alem 2 para evitar mistura de runs.
    data_dir = repo_root / "automation" / "data"
    try:
        (data_dir / "logs.json").unlink(missing_ok=True)
        (data_dir / "patients.db").unlink(missing_ok=True)
    except Exception:
        pass

    from backend.app import create_app

    app = create_app()
    app.config.update(TESTING=True)
    client = app.test_client()

    # 1) Status
    status = _get_json(client, "/api/status")

    # 2) Conversa (simulando "humano")
    user_id = "smoke_user"
    convo: list[dict[str, Any]] = []

    def chat(text: str) -> dict[str, Any]:
        r = _post_json(client, "/api/message", {"message": text, "user_id": user_id})
        convo.append({"ts": _now_iso(), "role": "user", "text": text})
        convo.append({"ts": _now_iso(), "role": "assistant", "text": r["json"].get("response")})
        return r

    # Conversa "humana" (inclui caso problemático reportado: dor no braço + resposta livre)
    chat("meu dente ta doendo")
    chat("to com dor no braço")
    chat("no direito")
    chat("voce nao sabe me responder ne")
    chat("sim ou nao o que????")
    chat("onde eu acho um médico????")

    # 3) Organizar informações (Ir Alem 1) + triagem (Fase 2)
    texto_base = (
        "Estou com dor no peito ha 2 horas, falta de ar leve e ansiedade. "
        "Medi pressao 150/95 e FC 88 bpm."
    )
    extract = _post_json(client, "/api/clinical/extract", {"text": texto_base})
    triage = _post_json(client, "/api/phase2/triage", {"text": texto_base})

    # 4) Monitoramento (Ir Alem 2)
    monitor_run = _post_json(client, "/api/monitor/run_once", {})
    monitor_logs = _get_json(client, "/api/monitor/logs")

    # 5) Vitals (Fase 3)
    vitals_ok = _post_json(client, "/api/phase3/vitals", {"temp": 36.9, "bpm": 72})
    vitals_alert = _post_json(client, "/api/phase3/vitals", {"temp": 39.2, "bpm": 130})

    # 6) Fase 4 (health-check)
    phase4_health = _get_json(client, "/api/phase4/health")

    report = {
        "generated_at": _now_iso(),
        "mode": "local",
        "status": status,
        "conversation": convo,
        "clinical_extract": extract,
        "phase2_triage": triage,
        "monitor_run_once": monitor_run,
        "monitor_logs": monitor_logs,
        "phase3_vitals_ok": vitals_ok,
        "phase3_vitals_alert": vitals_alert,
        "phase4_health": phase4_health,
    }

    (evid_dir / "local_smoke_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # Transcript legivel
    md_lines = [
        "# Smoke Test (Modo LOCAL)",
        "",
        f"Gerado em: `{report['generated_at']}`",
        "",
        "## Conversa",
        "",
    ]
    for msg in convo:
        who = "Usuário" if msg["role"] == "user" else "CardioIA"
        md_lines.append(f"**{who}:** {msg['text']}")
        md_lines.append("")

    md_lines += [
        "## Organizar Informações (Resumo)",
        "",
        f"Fonte: `{extract['json'].get('source')}`",
        "",
        "```json",
        json.dumps(
            {
                "summary": extract["json"].get("summary"),
                "triage": extract["json"].get("triage"),
                "structured": extract["json"].get("structured"),
            },
            ensure_ascii=False,
            indent=2,
        ),
        "```",
        "",
        "## Monitoramento (Últimos logs)",
        "",
        "```json",
        json.dumps((monitor_logs["json"].get("logs") or [])[-5:], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Vitals (Fase 3)",
        "",
        "```json",
        json.dumps({"ok": vitals_ok["json"], "alert": vitals_alert["json"]}, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Fase 4 (Health)",
        "",
        "```json",
        json.dumps(phase4_health["json"], ensure_ascii=False, indent=2),
        "```",
    ]

    (evid_dir / "local_smoke_transcript.md").write_text("\n".join(md_lines), encoding="utf-8")

    # HTML simples para "print" do chat
    html = [
        "<!doctype html>",
        "<html lang='pt-BR'>",
        "<meta charset='utf-8'/>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'/>",
        "<title>CardioIA - Smoke Local</title>",
        "<style>",
        "  :root{--bg:#0b1220;--panel:rgba(255,255,255,.06);--stroke:rgba(255,255,255,.12);--text:rgba(255,255,255,.92);--muted:rgba(255,255,255,.65);--a:#ff3b6b;--b:#ff7a2f;}",
        "  body{margin:0;font-family:system-ui,Segoe UI,Roboto,Arial; background: radial-gradient(1200px 800px at 15% 10%, rgba(255,59,107,.28), transparent 60%), radial-gradient(900px 700px at 80% 20%, rgba(255,122,47,.22), transparent 55%), linear-gradient(180deg, #0b1220, #0d1b2a); color:var(--text);}",
        "  .wrap{max-width:980px;margin:0 auto;padding:28px 18px 36px;}",
        "  .card{border:1px solid var(--stroke); border-radius:22px; background:linear-gradient(180deg, rgba(255,255,255,.07), rgba(255,255,255,.04)); box-shadow:0 24px 80px rgba(0,0,0,.55); overflow:hidden;}",
        "  header{display:flex;justify-content:space-between;align-items:flex-end;gap:12px;padding:18px 18px 14px;border-bottom:1px solid var(--stroke);}",
        "  h1{margin:0;font-size:18px;letter-spacing:.2px}",
        "  .pill{border:1px solid var(--stroke);border-radius:999px;padding:6px 10px;font-weight:800;font-size:12px;background:rgba(0,0,0,.22)}",
        "  .msgs{padding:16px;display:grid;gap:12px;}",
        "  .row{display:flex;}",
        "  .row.user{justify-content:flex-end;}",
        "  .bub{max-width:76%;border-radius:18px;padding:12px 14px 10px;border:1px solid var(--stroke);background:rgba(255,255,255,.06)}",
        "  .row.user .bub{background:linear-gradient(135deg, rgba(255,59,107,.38), rgba(255,122,47,.28)); border-color:rgba(255,122,47,.25)}",
        "  .meta{margin-top:6px;font-size:11px;color:rgba(255,255,255,.6);text-align:right}",
        "  .section{margin-top:14px;}",
        "  .k{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.7);font-weight:900}",
        "  pre{white-space:pre-wrap; word-break:break-word; background:rgba(0,0,0,.22); border:1px solid rgba(255,255,255,.1); padding:12px; border-radius:14px; color:rgba(255,255,255,.86)}",
        "</style>",
        "<body>",
        "<div class='wrap'>",
        "<div class='card'>",
        "<header>",
        "<div><div class='k'>Smoke Test</div><h1>CardioIA (Modo LOCAL)</h1></div>",
        "<div class='pill'>Gerado automaticamente</div>",
        "</header>",
        "<div class='msgs'>",
    ]
    for i in range(0, len(convo), 2):
        u = convo[i]
        a = convo[i + 1]
        html += [
            "<div class='row user'><div class='bub'>"
            + (u["text"] or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            + "<div class='meta'>Usuário</div></div></div>",
            "<div class='row assistant'><div class='bub'>"
            + (a["text"] or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
            + "<div class='meta'>CardioIA</div></div></div>",
        ]

    html += [
        "</div>",
        "<div class='msgs section'>",
        "<div class='k'>Organizar informações (resumo)</div>",
        "<pre>"
        + json.dumps(
            {
                "source": extract["json"].get("source"),
                "summary": extract["json"].get("summary"),
                "triage": extract["json"].get("triage"),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "</pre>",
        "</div>",
        "</div>",
        "</div>",
        "</body>",
        "</html>",
    ]

    (evid_dir / "local_smoke_chat.html").write_text("\n".join(html), encoding="utf-8")

    print(f"Wrote: {evid_dir / 'local_smoke_report.json'}")
    print(f"Wrote: {evid_dir / 'local_smoke_transcript.md'}")
    print(f"Wrote: {evid_dir / 'local_smoke_chat.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

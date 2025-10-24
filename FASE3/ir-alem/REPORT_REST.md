# IR ALÉM 1 — Relatório (REST + E‑mail)

## Objetivo

Implementar cliente/servidor REST para sinais vitais com lógica de risco (taquicardia, febre) e disparo de e‑mail.

## Arquitetura

- FastAPI `POST /vitals` (arquivo `ir-alem/rest_alerts.py`).
- Regras: bpm > 120 → Taquicardia; temp > 38 → Febre.
- Envio de e‑mail: SMTP via variáveis de ambiente ou simulado (log).
- Cliente de testes: `ir-alem/client.py` (gera amostras e envia ao endpoint).

## Execução

1) `pip install -r ir-alem/requirements.txt`
2) Servidor: `uvicorn ir-alem.rest_alerts:app --reload`
3) Cliente: `python ir-alem/client.py`

## Evidências (esperadas)

- Log do servidor com retorno `{ "risk": "alto", "alerts": ["Taquicardia"], ... }` para casos com bpm > 120.
- Log de e‑mail simulado: linha iniciando com `[EMAIL-SIM]` (se SMTP não configurado).

## Conclusões

O fluxo REST permite integrar automação e alertas de forma simples e clara, alinhando‑se ao enunciado “IR ALÉM 1”.


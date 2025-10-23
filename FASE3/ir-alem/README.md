# IR ALÉM 1 — REST + E‑mail

Este módulo simula consumo/envio de dados de sinais vitais via API REST em Python, aplica lógica de risco (taquicardia, febre) e dispara e‑mail em caso de alerta.

## Requisitos

- Python 3.9+
- `pip install -r requirements.txt`

## Executar o servidor

- `uvicorn ir-alem.rest_alerts:app --reload`
- Endpoint: `POST /vitals` com JSON `{ "temp": 36.8, "bpm": 72 }`
- Resposta: `{ "risk": "baixo|alto", "alerts": [..], "email": {..} }`

## Executar o cliente

- Em outro terminal: `python ir-alem/client.py`
- Envia amostras periódicas e exibe alertas retornados.

## Configurar e‑mail (opcional)

Defina variáveis de ambiente para envio real via SMTP (TLS):

- `SMTP_HOST`, `SMTP_PORT` (587), `SMTP_USER`, `SMTP_PASS`
- `FROM_EMAIL`, `TO_EMAIL`

Sem essas variáveis, o envio é simulado e apenas logado no console.


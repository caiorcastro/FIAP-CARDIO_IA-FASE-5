# Fase 3 — Parte 2: MQTT e Dashboard (Node‑RED)

Este relatório descreve o fluxo de comunicação MQTT e a configuração do dashboard no Node‑RED.

## Fluxo de comunicação

- Dispositivo (ESP32) publica leituras no tópico `cardioia/grupo1/vitals`.
- Broker: `broker.hivemq.com:1883` (público, sem autenticação, para prototipagem).
- Payload JSON por leitura: `{ "ts": 12345, "temp": 36.9, "hum": 55.0, "bpm": 72 }`.
- Node‑RED consome o tópico, parseia JSON e alimenta widgets do dashboard.

## Dashboard

- Gráfico (line chart) de BPM ao longo do tempo.
- Gauge de Temperatura (faixas: normal ≤ 37.5, atenção ≤ 38, alerta > 38).
- Alerta visual quando `bpm > 120` ou `temp > 38`.

## Nós principais

- `mqtt in` → `json` → `ui_chart`, `ui_gauge`, `switch` → `ui_text`
- `debug` para inspeção de mensagens.

## Arquivo do fluxo

- `FASE3/node-red/flow.json` (importar pelo menu do Node‑RED).

## Observações

- Em ambientes de produção, usar broker privado com TLS/autenticação.
- Limites de alerta podem ser ajustados diretamente no nó `switch`.
- Opcional: exportar dados para um banco de séries temporais (e.g., InfluxDB) e visualizar no Grafana.


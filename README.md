# CARDIO‑IA — FASE 3 (Monitoramento Contínuo IoT)

Este repositório contém a entrega da Fase 3 do projeto CardioIA, conforme o enunciado (ESP32 no Wokwi com 2 sensores, SPIFFS com resiliência offline, envio MQTT e dashboard em Node‑RED), além dos desafios "Ir Além" (REST + e‑mail; séries temporais).

- Pasta principal: `FASE3/`
- Integrantes: ver `CONTRIBUTORS.md`
- Fase 2 (referência): https://github.com/Wellbrito29/CardioIA-diagnostic-

## Como executar

- Wokwi (ESP32): importe `FASE3/wokwi/` no https://wokwi.com e inicie a simulação.
- Node‑RED: importe `FASE3/node-red/flow.json` e acesse o dashboard.
- REST + E‑mail: siga `FASE3/ir-alem/README.md` para executar servidor e cliente.
- Notebook: abra `FASE3/notebooks/phase3_time_series.ipynb` no Jupyter.

## Observância ao enunciado

- Parte 1 (Edge): 2 sensores (DHT22 obrigatório + botão/BPM), SPIFFS com fila e limite, resiliência offline implementada e relatada em `FASE3/reports/REPORT_EDGE.md`.
- Parte 2 (Fog/Cloud): MQTT (HiveMQ público para protótipo), Node‑RED com gráfico BPM, gauge de temperatura e alerta visual; documentação em `FASE3/reports/REPORT_MQTT_DASH.md`.
- Ir Além 1: Cliente/servidor REST com lógica de risco e e‑mail (simulado/SMTP real via env vars).
- Ir Além 2: Notebook com comparação de métodos simples de detecção de anomalias.

## Colaboração (Fase 2 + Fase 3)

- Adicionar colaboradores do repositório da Fase 2 neste repositório no GitHub (Settings → Collaborators). Lista sugerida em `CONTRIBUTORS.md`.
- Padrões de contribuição: issues com etiqueta `[fase3]`, PRs por funcionalidade, revisão cruzada entre membros.


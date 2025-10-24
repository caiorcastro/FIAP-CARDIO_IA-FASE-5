# CardioIA — Fase 3: Monitoramento Contínuo de Saúde com IoT

## Visão Geral do Projeto

Protótipo completo: ESP32 (Wokwi) com DHT22 + botão (BPM), SPIFFS com resiliência offline, publicação segura em MQTT (HiveMQ Cloud TLS 8883), dashboard em tempo real (Node‑RED) e automação de alertas (REST + e‑mail). Notebook demonstra detecção de anomalias simples em séries temporais.

## Arquitetura (resumo)

- ESP32 (Wokwi): DHT22 + botão (BPM) → SPIFFS com fila e resiliência
- MQTT (HiveMQ Cloud, TLS 8883) com validação de certificado
- Node‑RED: fluxo + dashboard (gráfico BPM, gauge temperatura, alerta)
- REST + e‑mail (FastAPI /vitals) com regra de risco (bpm>120, temp>38)
- Notebook de séries temporais (anomalias de BPM/temperatura)

## Estrutura

```
FASE3/
├── ir-alem/              # REST + e‑mail (IR ALÉM 1)
├── node-red/             # Fluxos (TLS e demo)
├── notebooks/            # Séries temporais (IR ALÉM 2)
├── reports/              # Relatórios + evidências (prints)
├── tools/                # Scripts de teste/captura
└── wokwi/                # ESP32 (Arduino) + diagrama
```

## Como Executar

1) Wokwi (ESP32)
- Crie `FASE3/wokwi/config.h` a partir de `config.example.h` com suas credenciais do HiveMQ Cloud.
- Importe `wokwi/` no Wokwi e clique em “Start the simulation”.
- Link público: https://wokwi.com/projects/445645684122269697

2) Node‑RED
- Importe `node-red/flow-hivemq-cloud.json` e preencha usuário/senha do HiveMQ Cloud.
- Acesse `http://127.0.0.1:1880/ui` para ver o dashboard.

3) REST + e‑mail
- `pip install -r ir-alem/requirements.txt`
- Servidor: `uvicorn ir-alem.rest_alerts:app --reload`
- Cliente: `python ir-alem/client.py`

4) Notebook
- `jupyter notebook` e abra `notebooks/phase3_time_series.ipynb`

## Evidências Visuais

| Wokwi (rodando) | Flush SPIFFS | Dashboard | Fluxo |
|---|---|---|---|
| ![](reports/images/wokwi_running.png) | ![](reports/images/esp32_flush_queue.png) | ![](reports/images/node_red_dashboard.png) | ![](reports/images/node_red_flow.png) |

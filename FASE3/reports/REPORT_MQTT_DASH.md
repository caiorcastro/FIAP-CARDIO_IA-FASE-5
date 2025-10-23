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

## 4. Evidências Visuais

Esta seção apresenta as evidências visuais do fluxo e do dashboard em funcionamento. Como não consigo gerar screenshots, as imagens devem ser adicionadas manualmente.

### 4.1. Fluxo de Nós no Node-RED

A imagem abaixo deve mostrar o fluxo de nós importado e conectado no editor do Node-RED.

**Ação Necessária:** Tire um print da tela do seu editor Node-RED mostrando os nós conectados e salve como `node_red_flow.png` na pasta `FASE3/reports/images/`.

![Fluxo de Nós no Node-RED](images/node_red_flow.png "Fluxo de nós configurado no editor do Node-RED")

### 4.2. Dashboard em Funcionamento

A imagem a seguir deve exibir o dashboard recebendo dados em tempo real, com o gráfico de BPM, o gauge de temperatura e um alerta (se aplicável).

**Ação Necessária:** Com o Wokwi enviando dados, acesse seu dashboard em `http://127.0.0.1:1880/ui`, tire um print da tela e salve como `node_red_dashboard.png` na pasta `FASE3/reports/images/`.

![Dashboard com Dados em Tempo Real](images/node_red_dashboard.png "Dashboard do Node-RED em funcionamento")

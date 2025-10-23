# Fase 3 — Parte 1: Edge Computing, SPIFFS e Resiliência

Este relatório descreve o fluxo de funcionamento do protótipo ESP32 no Wokwi, com ênfase no armazenamento local (SPIFFS) e na resiliência offline.

## Arquitetura

- Sensores: DHT22 (temperatura/umidade — obrigatório) + botão (simula batimentos cardíacos)
- MCU: ESP32 DevKit V1 (Wokwi)
- Armazenamento: SPIFFS (fila `queue.txt`)
- Conectividade: Wi‑Fi (simulado) + MQTT
- Publicação: JSON por leitura em `cardioia/grupo1/vitals`

## Fluxo

1. Leitura periódica dos sensores (3s): `temp`, `hum`, `bpm` (estimado por cliques nos últimos 10s * 6).
2. Construção do JSON: `{ ts, temp, hum, bpm }`.
3. Se online+MQTT: publica; caso contrário, armazena a linha JSON em `queue.txt`.
4. Na reconexão: esvazia a fila (publica linhas pendentes) e reescreve arquivo apenas com falhas.
5. Limite de fila: 300 amostras. Quando excedido, descarta do início (política FIFO).

## Resiliência offline

- O dispositivo continua coletando dados mesmo sem Wi‑Fi.
- Ao voltar a ficar online, sincroniza os dados pendentes via MQTT.
- Limite de fila configurável para adequar ao modelo de negócio.

## Arquivos

- Código principal: `FASE3/wokwi/sketch.ino`
- Diagrama Wokwi: `FASE3/wokwi/diagram.json`
- Config: `FASE3/wokwi/wokwi.toml`

## Observações

- O SSID padrão para simulação é `Wokwi-GUEST`. Ajuste `WIFI_SSID/WIFI_PASS` para cenários reais.
- O botão incrementa batimentos; o DHT22 gera temperatura/umidade. Leituras inválidas são suavemente simuladas.


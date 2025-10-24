# FIAP - Faculdade de Informática e Administração Paulista

<p align="center">
  <a href="https://www.fiap.com.br/">
    <img src="https://www.fiap.com.br/wp-content/themes/fiap2016/images/sharing/fiap.png" alt="FIAP" border="0" width="40%" height="40%">
  </a>
</p>

<br>

# CardioIA — Fase 3: Monitoramento Contínuo IoT

## Grupo 1 — CardioIA

## Integrantes
- <a href="https://www.linkedin.com/in/caiorcastro/">Caio Rodrigues Castro</a>
- <a href="https://www.linkedin.com/in/digitalmanagerfelipesoares/">Felipe Soares Nascimento</a>
- <a href="https://www.linkedin.com/in/fernando-segregio/">Fernando Miranda Segregio</a>
- <a href="https://www.linkedin.com/in/mralmeida">Mario Roberto Silva de Almeida</a>
- Wellington Nascimento de Brito

## Professores
### Tutor(a)
- <a href="https://www.linkedin.com/in/leonardoorabona/">Leonardo Ruiz Orabona</a>
### Coordenador(a)
- <a href="https://www.linkedin.com/in/profandregodoi/">André Godoi</a>

## Descrição
O projeto implementa um protótipo funcional de monitoramento cardiológico contínuo, integrando ESP32 (Wokwi), armazenamento local (SPIFFS) com resiliência offline, transmissão segura para a nuvem via MQTT (HiveMQ Cloud, TLS 8883), visualização em tempo real (Node‑RED Dashboard) e automação de alertas (REST + e‑mail). Complementarmente, há um notebook com análise simplificada de séries temporais (detecção de anomalias em BPM/temperatura).

## Arquitetura

```mermaid
flowchart TD
  A[ESP32 (Wokwi)
  DHT22 + Botão/BPM
  SPIFFS + Resiliência] -->|TLS 8883 / JSON| B[(HiveMQ Cloud MQTT)]
  B --> C[Node‑RED
  Flow + Dashboard]
  C --> D[UI em tempo real
  Gráfico BPM / Gauge Temp / Alertas]
  A -.->|Evidências| E[Flush da fila SPIFFS
  após reconexão]
  F[Cliente REST] --> G[FastAPI /vitals
  Regras de risco]
  G --> H[E‑mail (SMTP)
  Simulado/Real]
```

Links rápidos:
- Wokwi (público): https://wokwi.com/projects/445645684122269697
- Node‑RED (local): http://127.0.0.1:1880/ui
- Tópico MQTT: `cardioia/grupo1/vitals`

## Estrutura de pastas
- `.github/`: automações e configs GitHub
- `assets/`: imagens e artefatos estáticos
- `config/`: arquivos de configuração (se aplicável)
- `document/`: relatórios e documentos do projeto (links para relatórios detalhados)
- `scripts/`: scripts auxiliares
- `src/`: código‑fonte (ver FASE3 na raiz)
- `FASE3/`: artefatos da Fase 3 (ESP32, Node‑RED, REST, Notebooks, Evidências)

## Como executar o código (Fase 3)
- Wokwi (ESP32): importe `FASE3/wokwi/` no https://wokwi.com e inicie a simulação. Configurar `config.h` a partir de `config.example.h` com as credenciais do HiveMQ Cloud.
- Node‑RED: importe `FASE3/node-red/flow-hivemq-cloud.json` (TLS 8883) e preencha usuário/senha; acesse `http://127.0.0.1:1880/ui`.
- REST + E‑mail: siga `FASE3/ir-alem/README.md` para executar servidor e cliente.
- Notebook: abra `FASE3/notebooks/phase3_time_series.ipynb` no Jupyter.

## Evidências Visuais

| Wokwi (rodando) | Node‑RED (Dashboard) | Node‑RED (Fluxo) |
|---|---|---|
| ![](FASE3/reports/images/wokwi_running.png) | ![](FASE3/reports/images/node_red_dashboard.png) | ![](FASE3/reports/images/node_red_flow.png) |

Evidência de pub/sub MQTT (TLS 8883): ver `FASE3/reports/evidence_mqtt.txt`.

## Documentos
- Ver `document/README.md` para links dos relatórios (Parte 1, Parte 2, IR ALÉM 1 e 2) e evidências.

## Histórico de lançamentos
- 0.1.0 — 2025‑10‑24
  - Entrega Fase 3 (ESP32+SPIFFS+MQTT TLS, Node‑RED, REST, Notebook) + evidências

## Licença
<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1"><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1">
<p xmlns:cc="http://creativecommons.org/ns#" xmlns:dct="http://purl.org/dc/terms/">
<a property="dct:title" rel="cc:attributionURL" href="https://github.com/lfusca/templateFiap">MODELO GIT FIAP</a> por <a rel="cc:attributionURL dct:creator" property="cc:attributionName" href="https://fiap.com.br">FIAP</a> está licenciado sob <a href="http://creativecommons.org/licenses/by/4.0/?ref=chooser-v1" target="_blank" rel="license noopener noreferrer" style="display:inline-block;">CC BY 4.0</a>.
</p>

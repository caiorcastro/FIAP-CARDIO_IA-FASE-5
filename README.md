# FIAP - Faculdade de Informatica e Administracao Paulista

<p align="center">
  <a href="https://www.fiap.com.br/">
    <img src="https://www.fiap.com.br/wp-content/themes/fiap2016/images/sharing/fiap.png" alt="FIAP" border="0" width="40%" height="40%">
  </a>
</p>

<br>

# CardioIA - Fase 3: Monitoramento Continuo IoT

## Grupo 1 - CardioIA

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
- <a href="https://www.linkedin.com/in/profandregodoi/">Andre Godoi</a>

## Descricao
Projeto de monitoramento cardiologico continuo: ESP32 (Wokwi) com DHT22 + botao (BPM), SPIFFS com fila e resiliencia offline, MQTT com TLS (HiveMQ Cloud), dashboard em Node-RED e alertas via REST + e-mail. Notebook simples de series temporais para anomalias (BPM/temperatura).

## Arquitetura (resumo)
- ESP32 (Wokwi): DHT22 + botao (BPM) -> SPIFFS com fila e resiliencia
- MQTT (HiveMQ Cloud, TLS 8883) com validacao de certificado
- Node-RED: fluxo + dashboard (grafico BPM, gauge temperatura, alerta)
- REST + e-mail (FastAPI /vitals) com regra de risco (bpm>120, temp>38)
- Notebook de series temporais (anomalias de BPM/temperatura)

Links rapidos:
- Wokwi (publico): https://wokwi.com/projects/445645684122269697
- Node-RED (local): http://127.0.0.1:1880/ui
- Topico MQTT: `cardioia/grupo1/vitals`

## Estrutura de pastas
- `.github/`: automatizacoes e configs GitHub
- `assets/`: imagens e artefatos estaticos
- `config/`: arquivos de configuracao (se aplicavel)
- `document/`: relatorios e documentos do projeto
- `scripts/`: scripts auxiliares
- `src/`: codigo-fonte
  - `FASE3/`: artefatos da Fase 3 (ESP32, Node-RED, REST, Notebooks, Evidencias)
  - `FASES/`: copias de referencia das fases anteriores (quando disponiveis)
  - `FASE4/`: artefatos da fase atual de visao computacional (ver abaixo)

## Como executar o codigo (Fase 3)
- Wokwi (ESP32): importe `FASE3/wokwi/` no https://wokwi.com e inicie a simulacao. Configure `config.h` a partir de `config.example.h` com as credenciais do HiveMQ Cloud.
- Node-RED: importe `FASE3/node-red/flow-hivemq-cloud.json` (TLS 8883) e preencha usuario/senha; acesse `http://127.0.0.1:1880/ui`.
- REST + E-mail: siga `FASE3/ir-alem/README.md` para executar servidor e cliente.
- Notebook: abra `FASE3/notebooks/phase3_time_series.ipynb` no Jupyter.

## Evidencias
- Pub/sub MQTT (TLS 8883): `FASE3/reports/evidence_mqtt.txt`.

## Documentos
- Ver `document/README.md` para links dos relatorios (Parte 1, Parte 2, IR ALEM 1 e 2) e evidencias.

## Repositorios das Fases Anteriores
- Fase 1: https://github.com/FernandoSegregio/CardioIA (inacessivel no momento; copia local pendente em `FASES/Fase1/`)
- Fase 2: https://github.com/Wellbrito29/CardioIA-diagnostic- (copia local em `FASES/Fase2/`)

## Fase 4 (Visao Computacional)
- Guia da fase: `FASE4/README.md`
- Notebook principal: `FASE4/notebooks/phase4_cv.ipynb` (pre-process + CNN simples + transfer learning)
- Prototipo Flask: `FASE4/app/app.py` (usa `model.pt` exportado do notebook)
- Relatorios, metricas e fairness: `FASE4/reports/` (inclui predict_example.json)

## Historico de lancamentos
- 0.1.0 - 2025-10-24
  - Entrega Fase 3 (ESP32+SPIFFS+MQTT TLS, Node-RED, REST, Notebook) + evidencias

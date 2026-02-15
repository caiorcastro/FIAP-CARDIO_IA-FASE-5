# CardioIA - Fase 5: Assistente Cardiológico Inteligente (Experiência do Paciente)

![CardioIA - Fase 5](document/fase5/assets/banner.svg)

Entrega acadêmica FIAP (Cap 1) baseada no enunciado em `enunciado-fase5.txt`.

Esta fase evolui o CardioIA para um **assistente conversacional** capaz de interagir em linguagem natural, organizar **informações clínicas** e integrar **NLP + automação + APIs + dados**.

Aviso: este protótipo **não substitui orientação médica**. Em caso de emergência, **ligue 192 (SAMU)**.

## Links Rápidos
- Checklist requisito -> evidência: `document/fase5/checklist_requisitos.md`
- Relatórios (MD + PDF): `document/fase5/README.md`
- Export (evidência) do assistente (modelo clássico): `watson_skill_export.json`
- Mapa do repositório (arquivo por arquivo): `document/fase5/mapa_repositorio.md`

## O Que Foi Entregue (Resumo)
- **Parte 1 (Watson + NLP)**:
  - Modelagem do assistente no Watson Assistant e export (intents/entities/dialog nodes)
  - Integração via backend Flask (API)
  - Relatório curto (1-2 páginas) em `document/fase5/relatorio_conversacional.pdf`
- **Parte 2 (Interface)**:
  - Interface web (React) integrada ao backend
  - Roteiro + campo para link do vídeo: `document/fase5/video_demo.md`
- **Ir Além 1 (GenAI)**:
  - Extração de informações clínicas de texto livre e saída estruturada (JSON)
  - Notebook + documento PDF em `document/fase5/ir-alem-1_extracao_clinica.pdf`
- **Ir Além 2 (RPA + Dados Híbridos)**:
  - Robô que lê dados relacionais (SQLite), detecta anomalias e registra logs em JSON (NoSQL)
  - Documento PDF em `document/fase5/ir-alem-2_rpa_dados_hibridos.pdf`

## Requisitos do Enunciado (Parte 1 e Parte 2)
Checklist completo: `document/fase5/checklist_requisitos.md`.

Parte 1 (Watson + NLP):
- Assistente conversacional usando IBM Watson Assistant: `backend/watson_service.py` + evidência `document/fase5/evidencias/watson_smoke_test.json`
- Modelagem (intents/entities/dialog nodes) como entregável acadêmico: `watson_skill_export.json`
- Fluxo coerente + fallback + exceções básicas: `watson_skill_export.json` + `backend/app.py` + `backend/mock_assistant.py`
- Integração via API (Flask): `backend/app.py` (`POST /api/message`)
- Relatório curto (1-2 páginas): `document/fase5/relatorio_conversacional.pdf`

Parte 2 (Interface):
- Interface web integrada ao backend: `frontend/` (build em `backend/static/`)
- Enviar mensagens e visualizar respostas: UI + `POST /api/message`
- Organização do projeto (boas práticas + estrutura): `document/fase5/mapa_repositorio.md`

## Modos de Execução (Por que existe “LOCAL”)
Para a banca conseguir testar sem depender de credenciais, o sistema roda em 2 modos:
- **WATSON**: usa o assistente publicado no IBM Watson Assistant (API V2).
- **LOCAL (offline)**: simula o fluxo conversacional usando `watson_skill_export.json` (intents/entities/dialog nodes) via `backend/mock_assistant.py`.

No vídeo, a recomendação é mostrar os dois: primeiro WATSON (publicado), depois LOCAL (fallback).

## Arquitetura (Fase 5)

### Visão Geral
```mermaid
flowchart LR
  U[Usuário] -->|mensagem| UI[Web Chat: frontend/]
  UI -->|POST /api/message| API[Flask: backend/app.py]
  API -->|SDK V2| W[IBM Watson Assistant]
  W --> API --> UI --> U

  subgraph Automação (Ir Além 2)
    DB[(SQLite: automation/data/patients.db)] --> RPA[Robot: automation/rpa_monitor.py]
    RPA -->|logs| LOG[(JSON: automation/data/logs.json)]
    RPA -->|opcional| G[Google Gemini]
  end
```

### Sequência (Chat)
```mermaid
sequenceDiagram
  participant User as Usuário
  participant UI as Frontend
  participant API as backend/app.py
  participant WA as Watson Assistant

  User->>UI: Digita mensagem
  UI->>API: POST /api/message {message,user_id}
  API->>WA: create_session (se necessário)
  API->>WA: message()
  WA-->>API: resposta + metadata
  API-->>UI: {response,intents,entities}
  UI-->>User: Renderiza resposta
```

## Estrutura do Repositório (Entrega Atual)
- `frontend/`: interface web (React + Vite)
- `backend/`: Flask + integração Watson + modo local (offline)
- `automation/`: RPA + SQLite + logs JSON
- `notebooks/`: notebook de GenAI (Ir Além 1)
- `document/fase5/`: relatórios exigidos (MD + PDF) + checklist
- `FASES ANTERIORES/`: histórico das fases anteriores
- `.env`: arquivo local (não versionado) com credenciais

## Tech Stack
- Python 3.10+ (recomendado)
- Flask
- React + Vite (frontend)
- IBM Watson Assistant SDK (`ibm-watson`)
- Google Gemini SDK (`google-generativeai`)
- SQLite (banco relacional, via `sqlite3`)
- JSON file (logs NoSQL)

## Configuração (.env)
Crie `.env` na raiz do repositório a partir de `.env.example`.

Variáveis:
- `WATSON_API_KEY`: API key das Service Credentials
- `WATSON_URL`: URL da instância (normalmente `.../instances/<id>`)
- `WATSON_ASSISTANT_ID`: ID do Assistant publicado
- `WATSON_ENVIRONMENT_ID`: Environment ID (GUID). Em algumas contas acadêmicas, ele pode coincidir com o próprio `WATSON_ASSISTANT_ID`.
- `ASSISTANT_ID`: compatibilidade (opcional). Se preenchido, o backend usa esse valor como assistant/environment quando você não quiser separar as variáveis.
- `GEMINI_API_KEY`: chave do Gemini (opcional para RPA/Ir Além)
- `CARDIOIA_ASSISTANT_MODE`: `watson` (padrão) ou `local` (offline)
- `WATSON_CONSOLE_URL`: opcional (aparece no botão “Watson IBM” da UI para abrir o seu projeto no console)

## Como Rodar

### 1. Backend + Frontend (Chat)
```powershell
pip install -r backend/requirements.txt
python run_server.py
```
Abra: `http://127.0.0.1:5000`

Opcional (para editar o frontend):
```powershell
cd frontend
npm install
npm run dev
```

### 2. Modo Local (Offline, sem credenciais)
```powershell
$env:CARDIOIA_ASSISTANT_MODE="local"
python run_server.py
```

### 3. Automação RPA (Ir Além 2)
```powershell
cd automation
python database_setup.py
python rpa_monitor.py
```
Saída:
- `automation/data/patients.db`
- `automation/data/logs.json`

### 4. Notebook GenAI (Ir Além 1)
```powershell
jupyter notebook notebooks/genai_extraction.ipynb
```

## Testes
```powershell
python -m pytest
```

## Como Atendemos o Enunciado (Ponto a Ponto)
Consulte:
- `document/fase5/checklist_requisitos.md`

## Evolução do CardioIA (Fases 2, 3 e 4 -> Fase 5)
Esta entrega é uma **evolução** das fases anteriores: a Fase 5 consolida a “porta de entrada” do paciente (conversa + triagem + encaminhamento).

- **Fase 2 (NLP + triagem / risco)**  
  Base do raciocínio clínico inicial e organização de sintomas. Evidências em `FASES ANTERIORES/Fase2/`.
- **Fase 3 (IoT + monitoramento contínuo)**  
  Contexto de sinais vitais e alertas em tempo real. Evidências em `FASES ANTERIORES/FASE3/`.
- **Fase 4 (Visão computacional)**  
  Módulo de apoio ao diagnóstico por imagem (quando aplicável). Evidências em `FASES ANTERIORES/FASE4/`.

Mapa detalhado (arquivo por arquivo): `document/fase5/mapa_repositorio.md`.

## Fases Anteriores (Histórico)
As fases anteriores estão organizadas em `FASES ANTERIORES/` para manter histórico e rastreabilidade.

```mermaid
timeline
  title CardioIA (Evolução por Fase)
  Fase 1 : Fundamentos e base de dados
  Fase 2 : NLP e triagem (IA)
  Fase 3 : IoT e monitoramento contínuo
  Fase 4 : Visão computacional (diagnóstico por imagem)
  Fase 5 : Assistente conversacional + GenAI + RPA
```

## Equipe
Grupo 15 (FIAP): ver `CONTRIBUTORS.md`.

## Evidências do Watson “vivo” (para a banca)
Mesmo com limitações de alguns planos/contas no Watson (endpoints administrativos podem retornar 404), a evidência principal é a conversa real via API:
- Script (gera evidência sem segredos): `scripts/watson_generate_evidence.py`
- Resultado: `document/fase5/evidencias/watson_smoke_test.json`
- Explicação do espelhamento (Watson vivo x export clássico): `document/fase5/evidencias/espelhamento_watson.md`

## Documentação no navegador (para o vídeo)
O backend também serve documentação local para facilitar a demonstração:
- `/docs/fase5/...` (ex: `/docs/fase5/relatorio_conversacional.pdf`)
- `/docs/anteriores/...` (ex: `/docs/anteriores/REPORT-DE-AVAN%C3%87O.MD`)
- `/docs/root/...` (ex: `/docs/root/CONTRIBUTORS.md`)

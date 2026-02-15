# Mapa do Repositório (Fase 5 + Fases Anteriores)

Objetivo deste documento: deixar explícito, arquivo por arquivo (no nível “útil”), **o que existe** no repositório e **por que existe**, para a banca não ter que adivinhar.

Obs: não listamos arquivos gerados automaticamente (ex: `__pycache__`, builds, etc.) além do que é relevante para rodar/demonstrar.

## Raiz do Projeto
- `README.md`  
  Documento principal da entrega da Fase 5 (como rodar, arquitetura, entregáveis e evidências).

- `enunciado-fase5.txt`  
  Enunciado completo usado como referência para checklist e entrega.

- `.env.example`  
  Modelo de variáveis de ambiente (sem segredos). O arquivo `.env` real é **local** e não é versionado.

- `.gitignore`  
  Ignora `.env`, `node_modules`, caches e arquivos auxiliares.

- `CONTRIBUTORS.md`  
  Lista de integrantes e acordos de colaboração (evidência de trabalho em equipe).

- `watson_skill_export.json`  
  Export “modelo clássico” do Watson, contendo **intents**, **entities** e **dialog_nodes** (entregável solicitado no enunciado).

- `run_server.py`  
  Entry-point para rodar a aplicação localmente a partir da raiz.

## Backend (Fase 5)
Pasta: `backend/`

- `backend/app.py`  
  Backend Flask:
  - `POST /api/message` (chat)
  - `GET /api/status` (status do modo)
  - `GET /api/config` (URL opcional do console Watson)
  - `GET /docs/...` (documentos para o vídeo)

- `backend/watson_service.py`  
  Integração com IBM Watson Assistant V2 (SDK oficial). Normaliza resposta e faz fallback de texto quando o Watson retorna mensagens “engessadas”.

- `backend/mock_assistant.py`  
  Modo **LOCAL (offline)** para demonstração/avaliação sem credenciais:
  - Lê o `watson_skill_export.json`
  - Usa intents e dialog_nodes para simular o fluxo

- `backend/requirements.txt`  
  Dependências Python necessárias para rodar backend, testes e integrações.

- `backend/tests/test_api.py`  
  Testes mínimos com `pytest` para provar que:
  - `/api/status` responde
  - mensagem vazia não quebra a conversa
  - roundtrip em modo local funciona

- `backend/static/`  
  Build do frontend (React). Isso permite rodar a entrega sem precisar de `npm run build` na banca.

## Frontend (Fase 5)
Pasta: `frontend/` (React + Vite + TypeScript)

- `frontend/src/ui/App.tsx`  
  Interface de chat (moderna) + modal “Sobre” com links para evidências e documentação.

- `frontend/src/ui/styles.css`  
  Estilo do chat (identidade visual própria).

- `frontend/vite.config.ts`  
  Configura o build para sair em `backend/static/` e proxy `/api` no modo dev.

- `frontend/package.json`  
  Scripts: `dev`, `build`, `preview`.

## Documentação (Fase 5)
Pasta: `document/fase5/`

- `document/fase5/relatorio_conversacional.md` e `.pdf`  
  Relatório curto (Parte 1) explicando fluxo, modelagem e integração.

- `document/fase5/checklist_requisitos.md`  
  Enunciado -> evidência (arquivo/rota/artefato).

- `document/fase5/video_demo.md`  
  Roteiro do vídeo (até 3 min) com passos e comandos.

- `document/fase5/ir-alem-1_extracao_clinica.md` e `.pdf`  
  “Ir Além 1”: extração de informações clínicas (GenAI).

- `document/fase5/ir-alem-2_rpa_dados_hibridos.md` e `.pdf`  
  “Ir Além 2”: automação (RPA), dados relacionais + logs JSON.

- `document/fase5/evidencias/`  
  Evidências “vivas” (sem segredos) do Watson publicado:
  - `watson_smoke_test.json`
  - `watson_environments.json` (pode retornar erro dependendo do plano)
  - `watson_environment_details.json` (pode retornar erro dependendo do plano)
  - `espelhamento_watson.md` (explica Watson vivo x export clássico)

- `document/fase5/assets/`  
  Artefatos visuais da documentação (ex: `banner.svg`).

## Scripts de Apoio (Fase 5)
Pasta: `scripts/`

- `scripts/generate_fase5_pdfs.py`  
  Gera PDFs a partir dos arquivos `.md` da Fase 5 (para facilitar entrega).

- `scripts/watson_discover_environment.py`  
  Tenta descobrir o `WATSON_ENVIRONMENT_ID`. Se endpoints administrativos falharem, faz fallback testável via `create_session`.

- `scripts/watson_generate_evidence.py`  
  Gera evidência do Watson “vivo”: cria sessão e envia prompts, salvando em JSON (sem segredos).

## Automação (Ir Além 2)
Pasta: `automation/`

- `automation/database_setup.py`  
  Cria um banco SQLite com pacientes e sinais vitais (relacional).

- `automation/rpa_monitor.py`  
  “Robô” que lê periodicamente o SQLite, detecta padrões/anomalias e grava logs em JSON (não-relacional).

## Notebook (Ir Além 1)
Pasta: `notebooks/`

- `notebooks/genai_extraction.ipynb`  
  Demonstra extração de informações clínicas e estruturação de saída em JSON usando GenAI.

## Fases Anteriores (Histórico e Evolução)
Pasta: `FASES ANTERIORES/`

- `FASES ANTERIORES/REPORT-DE-AVANÇO.MD`  
  Relatório consolidado das fases anteriores (2, 3 e 4), usado para contextualizar a evolução do CardioIA.

### Fase 2 (NLP + Triagem)
Pasta: `FASES ANTERIORES/Fase2/`
- `FASES ANTERIORES/Fase2/src/diagnose.py` (extração de sintomas)
- `FASES ANTERIORES/Fase2/notebooks/risk_classifier.ipynb` (classificação de risco)
- `FASES ANTERIORES/Fase2/portal/` (frontend React da fase 2)

### Fase 3 (IoT + Monitoramento)
Pasta: `FASES ANTERIORES/FASE3/`
- `wokwi/` (ESP32 simulado)
- `node-red/` (fluxos + dashboard)
- `reports/` (evidências e relatórios)
- `notebooks/` (séries temporais)

### Fase 4 (Visão Computacional)
Pasta: `FASES ANTERIORES/FASE4/`
- `notebooks/` (pipeline CV)
- `app/` (Flask simples para servir modelo)
- `reports/` (métricas + discussões)


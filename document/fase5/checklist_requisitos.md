# Checklist de Requisitos (Enunciado -> Evidência)

Baseado em `enunciado-fase5.txt`.

## Parte 1 - Assistente Conversacional com NLP
- Desenvolver assistente no Watson Assistant (intents/entities/dialog nodes)
  - Evidência (export): `watson_skill_export.json`
- Evidência “viva” do Watson publicado (para o vídeo)
  - Smoke test (JSON): `document/fase5/evidencias/watson_smoke_test.json`
  - Espelhamento (explicação): `document/fase5/evidencias/espelhamento_watson.md`
- Fluxo coerente, respostas contextualizadas, exceções básicas
  - Fluxo (local/offline baseado no export): `backend/mock_assistant.py`
- Integração Watson <-> backend (Flask)
  - Backend Flask: `backend/app.py`
  - Serviço Watson SDK: `backend/watson_service.py`
  - Endpoint: `POST /api/message`
- Testes automatizados (mínimos, mas objetivos)
  - `backend/tests/test_api.py`
- Entregáveis
  - Código-fonte backend: `backend/`
  - Export/Config do assistente (JSON): `watson_skill_export.json`
  - Relatório curto: `document/fase5/relatorio_conversacional.md` (e PDF)

## Parte 2 - Interface
- Interface simples integrada ao backend
  - Frontend (React): `frontend/`
  - Build servido pelo Flask: `backend/static/`
- Projeto organizado + boas práticas
  - Estrutura na raiz (Fase 5): `frontend/`, `backend/`, `automation/`, `notebooks/`, `document/fase5/`
- Vídeo curto (até 3 min)
  - Instruções: `document/fase5/video_demo.md`

## Ir Além 1 - GenAI (Extração de Informações Clínicas)
- Prompting + IA Generativa
  - Notebook: `notebooks/genai_extraction.ipynb`
- Extrair infos relevantes e estruturar saída (JSON)
  - Exemplo e parsing: `notebooks/genai_extraction.ipynb`
- Conexão com o protótipo (Fase 5)
  - Endpoint: `POST /api/clinical/extract` (`backend/app.py` + `backend/clinical_extraction.py`)
  - UI: aba "Organizar informações" (`frontend/src/ui/App.tsx`)
- Entregáveis
  - Notebook/código: `notebooks/genai_extraction.ipynb`
  - Documento PDF explicando fluxo: `document/fase5/ir-alem-1_extracao_clinica.md` (e PDF)

## Ir Além 2 - RPA + IA + Dados Híbridos
- Ler dados clínicos periodicamente de banco relacional
  - SQLite + schema + seed: `automation/database_setup.py` (relacional)
- Banco não relacional para logs/metadados/mensagens
  - Logs JSON (NoSQL): `automation/data/logs.json` (gerado pelo robô)
- IA simples para padrões/anomalias
  - Regras de anomalia (PA/FC) + geração via Gemini: `automation/rpa_monitor.py`
- Rastreabilidade
  - Campos de log (timestamp/paciente/vitais/ação): `automation/rpa_monitor.py`
- Entregáveis
  - Código automação: `automation/`
  - Estruturas dos bancos: `automation/database_setup.py` e `automation/rpa_monitor.py`
  - Relatório técnico: `document/fase5/ir-alem-2_rpa_dados_hibridos.md` (e PDF)
- Conexão com o protótipo (Fase 5)
  - Ler logs: `GET /api/monitor/logs`
  - Rodar 1 ciclo do robô: `POST /api/monitor/run_once`
  - UI: aba "Monitoramento" (`frontend/src/ui/App.tsx`)

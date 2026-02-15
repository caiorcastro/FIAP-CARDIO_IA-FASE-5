# AGENTS.md - CardioIA (FIAP) - Fase 5

## Objetivo
Este repositório contém o projeto CardioIA (FIAP) com histórico das fases anteriores e a **entrega atual: Fase 5**.

Ponto de entrada da entrega:
- `FASE5/README.md`
- `enunciado-FASE5.pdf`

## Estrutura Relevante (Fase 5)
- `frontend/`: frontend (React + Vite) com interface de chat
- `backend/`: backend Flask (API `/api/message`)
- `automation/`: RPA + SQLite + logs JSON (Ir Além 2)
- `notebooks/`: notebook de GenAI (Ir Além 1)
- `watson_skill_export.json`: export do assistente no modelo clássico (intents/entities/dialog_nodes)

Compatibilidade (estrutura antiga):
- `FASE5/` pode conter apenas `.env` local e arquivos auxiliares.

## Variáveis de Ambiente
Arquivos `.env` são ignorados por `.gitignore` e **não devem ser versionados**.

Local esperado:
- `./.env` (recomendado)
- `FASE5/.env` (compatibilidade)

Exemplo:
- `.env.example`

Variáveis:
- `WATSON_API_KEY`
- `WATSON_URL`
- `ASSISTANT_ID` (ID do Assistant publicado)
- `GEMINI_API_KEY`

Modo de execução do assistente (para avaliação sem credenciais):
- `CARDIOIA_ASSISTANT_MODE=mock` (offline)
- `CARDIOIA_ASSISTANT_MODE=watson` (padrão)

## Como Rodar (Fase 5)
Backend + Frontend:
```powershell
cd backend
pip install -r requirements.txt
python app.py
```
Abrir:
- `http://127.0.0.1:5000`

Opcional (se quiser editar a interface React):
```powershell
cd frontend
npm install
npm run dev
```

Modo mock:
```powershell
$env:CARDIOIA_ASSISTANT_MODE="mock"
cd backend
python app.py
```

RPA:
```powershell
cd automation
python database_setup.py
python rpa_monitor.py
```

## Convenções
- Evite colocar credenciais em arquivos versionados.
- Se for necessário demonstrar configurações, use `*.example` e placeholders.

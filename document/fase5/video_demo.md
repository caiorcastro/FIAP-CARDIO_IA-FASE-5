# Vídeo de Demonstração (até 3 minutos)

## O que mostrar (roteiro sugerido)
1. Servidor rodando:
   - `pip install -r backend/requirements.txt`
   - `python run_server.py`
2. Abertura do chat em `http://127.0.0.1:5000`
3. Mostrar o badge “Modo: WATSON” (ou “LOCAL” se estiver offline)
4. Fluxo conversacional (exemplo de 3 minutos):
   - Saudação
   - Agendamento (perguntar data e confirmar)
   - Emergência (dor no peito -> pergunta -> orientação)
5. Evidência “viva” (opcional, mas forte para banca):
   - Rodar `python scripts/watson_generate_evidence.py`
   - Abrir `document/fase5/evidencias/watson_smoke_test.json` (sem segredos)
6. (Opcional) Rodar o RPA:
   - `python automation/database_setup.py`
   - `python automation/rpa_monitor.py`
   - Mostrar `automation/data/logs.json`

## Dica (se o Watson falhar na hora)
Você pode alternar para o modo offline sem mudar o frontend:
- `set CARDIOIA_ASSISTANT_MODE=local` (Windows CMD) ou `$env:CARDIOIA_ASSISTANT_MODE="local"` (PowerShell)
- Reinicie o servidor (`python run_server.py`)

## Link do vídeo
- Suba no YouTube (não listado) ou Google Drive e cole aqui:
  - **Link:** TODO

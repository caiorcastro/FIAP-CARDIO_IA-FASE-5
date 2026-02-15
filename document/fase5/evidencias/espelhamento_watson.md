# Evidência e Espelhamento (Watson “vivo” x Export JSON)

Este projeto entrega **dois artefatos complementares**:

1. **Watson publicado (vivo)**: o assistente em execução no IBM Watson Assistant (acessado via API V2).  
   Evidência técnica: `document/fase5/evidencias/watson_smoke_test.json`

2. **Modelo clássico solicitado no enunciado**: export em JSON com **intents, entities e dialog nodes**.  
   Evidência acadêmica: `watson_skill_export.json`

## Por que existem 2 evidências?
Na prática (especialmente em contas acadêmicas/lite), nem sempre é possível publicar/operar o mesmo fluxo no Watson usando exatamente o “modelo clássico” com **intents + entities + dialog nodes** de forma idêntica.

Por isso:
- Mantemos o **export clássico** (atende o que o enunciado pede como entregável).
- Mantemos o **Watson vivo** (atende a demonstração prática no vídeo e a integração via API).

## Como validar no vídeo (passo a passo)
1. Abrir a interface local (`http://127.0.0.1:5000`) em modo Watson.
2. Mostrar o status no topo (pílula “Modo: WATSON”).
3. Fazer 3 mensagens:
   - “Olá”
   - “Quero agendar uma consulta”
   - “Estou com dor no peito”
4. Mostrar o arquivo de evidência gerado pelo script:
   - `document/fase5/evidencias/watson_smoke_test.json`

## Tabela de equivalência (alto nível)
O conteúdo de intenção/fluxo é equivalente, apesar de o Watson (em Actions) retornar identificadores internos diferentes (ex: `action_..._intent_...`).

- **Saudação**
  - Export clássico: intent `saudacao` + nó de diálogo `#saudacao`
  - Watson vivo: responde com saudação e apresenta escopo do assistente

- **Agendamento**
  - Export clássico: intent `agendar_consulta` + nó `#agendar_consulta` + coleta de data `@sys-date`
  - Watson vivo: pergunta a data (“Para qual data você gostaria de agendar?”)

- **Emergência (dor no peito)**
  - Export clássico: intent `dor_no_peito` + nó `#dor_no_peito` e confirmação (sim/não/sintomas)
  - Watson vivo: pergunta sobre irradiação e náusea, sinalizando urgência

## Script de evidência (sem segredos)
O script abaixo cria sessão e envia prompts ao Watson para registrar evidência “ao vivo”:
- `scripts/watson_generate_evidence.py`

Ele **não grava API key** em nenhum arquivo.


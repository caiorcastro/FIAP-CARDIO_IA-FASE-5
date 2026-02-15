
import os
from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core.api_exception import ApiException
from dotenv import load_dotenv

# Carrega variáveis de ambiente procurando em locais comuns:
# - `./.env` (raiz do repo)
# - `./FASE5/.env` (compatibilidade com estrutura antiga)
# - `.env` no diretório atual (fallback)
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_CANDIDATE_ENVS = [
    os.path.join(_REPO_ROOT, ".env"),
    os.path.join(_REPO_ROOT, "FASE5", ".env"),
    os.path.join(os.path.dirname(__file__), ".env"),
]

for _p in _CANDIDATE_ENVS:
    load_dotenv(_p)

class WatsonService:
    def __init__(self):
        api_key = os.getenv("WATSON_API_KEY")
        url = os.getenv("WATSON_URL")
        # SDK atual do Watson Assistant V2 exige assistant_id + environment_id.
        # Compatibilidade: se só existir ASSISTANT_ID, usamos o mesmo valor para os dois.
        self.assistant_id = os.getenv("WATSON_ASSISTANT_ID") or os.getenv("ASSISTANT_ID")
        self.environment_id = os.getenv("WATSON_ENVIRONMENT_ID") or os.getenv("ASSISTANT_ID")
        
        if not api_key or not url or not self.assistant_id or not self.environment_id:
            raise ValueError(
                "As chaves do Watson (API_KEY, URL, ASSISTANT_ID/ASSISTANT_ID+ENVIRONMENT_ID) não estão configuradas no .env"
            )

        authenticator = IAMAuthenticator(api_key)
        self.assistant = AssistantV2(
            version='2021-06-14',
            authenticator=authenticator
        )
        self.assistant.set_service_url(url)

    def create_session(self):
        """Cria uma nova sessão com o assistente."""
        try:
            session = self.assistant.create_session(
                assistant_id=self.assistant_id,
                environment_id=self.environment_id,
            ).get_result()
            return session['session_id']
        except Exception as e:
            print(f"Erro ao criar sessão: {e}")
            return None


    def send_message(self, session_id, message_text, user_id=None):
        """Envia mensagem do usuário para o Watson e retorna a resposta."""
        # Se não tiver ID configurado ou der erro de conexão, retorna erro real (SEM LOCAL)
        if not self.assistant_id or not self.environment_id:
            return {"text": "Erro: Watson não configurado no .env. Configure ASSISTANT_ID (ou WATSON_ASSISTANT_ID + WATSON_ENVIRONMENT_ID)."}

        try:
            response = self.assistant.message(
                assistant_id=self.assistant_id,
                environment_id=self.environment_id,
                session_id=session_id,
                user_id=user_id,
                input={
                    'message_type': 'text',
                    'text': message_text,
                    'options': {
                        'return_context': True
                    }
                }
            ).get_result()

            if response['output']['generic']:
                text_response = response['output']['generic'][0]['text']
            else:
                text_response = "Desculpe, não entendi. Pode repetir?"

            # Normaliza quebras de linha que às vezes vêm em HTML.
            if isinstance(text_response, str):
                text_response = (
                    text_response.replace("<br />", "\n")
                    .replace("<br/>", "\n")
                    .replace("<br>", "\n")
                )

                # Fallback mais humano quando o Watson retorna mensagens "de menu" (comum em Actions).
                low = text_response.strip().lower()
                if "selecione uma opção válida" in low or low in ["eu não entendi.", "nao entendi.", "não entendi."]:
                    text_response = (
                        "Eu não entendi completamente, mas eu sigo com você.\n\n"
                        "Você quer:\n"
                        "- **agendar uma consulta**\n"
                        "- falar sobre **dor no peito**\n"
                        "- entender **pressão alta**\n\n"
                        "Me diga o que faz mais sentido agora."
                    )

            return {
                "text": text_response,
                "intents": response['output'].get('intents', []),
                "entities": response['output'].get('entities', [])
            }

        except ApiException as e:
            # Sessões do Watson expiram; nesse caso o backend pode recriar a sessão e reenviar 1 vez.
            msg = str(getattr(e, "message", "") or str(e))
            if getattr(e, "code", None) in [404, 400] and "session" in msg.lower():
                return {"text": "Sessão expirada. Recriando...", "error_type": "invalid_session"}
            print(f"Erro na nuvem Watson (ApiException): {e}")
            return {"text": f"Erro de comunicação com o Watson: {msg}"}

        except Exception as e:
            print(f"Erro na nuvem Watson: {e}")
            return {"text": f"Erro de comunicação com o Watson: {str(e)}"}

# Teste rápido se executado diretamente
if __name__ == "__main__":
    try:
        watDiv = WatsonService()
        sess_id = watDiv.create_session()
        print(f"Sessão criada: {sess_id}")
        resp = watDiv.send_message(sess_id, "Olá")
        print(f"Bot: {resp['text']}")
    except Exception as e:
        print(f"Erro no teste: {e}")

import streamlit as st
from openai import OpenAI
import fitz
import os

# ===================== Bot =====================
class Bot:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.file_context = None
        self.client = OpenAI(api_key=api_key) if api_key else None

        self.load_file_context()

    def set_api_key(self, api_key):
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
        return "API Key atualizada com sucesso."

    def read_pdf(self, file_path):
        text = ""
        try:
            with fitz.open(file_path) as pdf:
                for page in pdf:
                    text += page.get_text()
            return text
        except Exception as e:
            return f"[Erro ao ler PDF: {e}]"

    def load_file_context(self, directory=None):
        if directory is None:
            directory = os.path.dirname(os.path.abspath(__file__))

        context = ""

        try:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)

                if filename.lower().endswith(".txt"):
                    with open(file_path, "r", encoding="utf-8") as f:
                        context += f"\n\n--- {filename} ---\n"
                        context += f.read()

                elif filename.lower().endswith(".pdf"):
                    context += f"\n\n--- {filename} ---\n"
                    context += self.read_pdf(file_path)

            if context:
                self.file_context = context
                return "Arquivos .txt e .pdf foram carregados com sucesso."
            else:
                return "Nenhum arquivo .txt ou .pdf encontrado no diretório."

        except Exception as e:
            return f"Erro ao carregar arquivos: {str(e)}"

    def ask_chatgpt(self, user_input):
        if not self.client:
            return "API Key não definida. Atualize a API."

        if not user_input.strip():
            return "Por favor, digite algo."

        try:
            messages = []
            if self.file_context:
                messages.append({
                    "role": "system",
                    "content": f"Use o seguinte contexto do arquivo para ajudar a responder: {self.file_context}"
                })
            messages.append({"role": "user", "content": user_input})

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Ajuste para o modelo que você quer usar
                messages=messages
            )
            bot_reply = response.choices[0].message.content.strip()
            return bot_reply

        except Exception as e:
            return f"Erro: {str(e)}"

# ===================== Interface =====================
def render_interface(bot):
    st.title("ChatGPT usando uma rag local")

    api_key_input = st.text_input("Digite sua OpenAI API Key:", type="password", key="api_key_input")
    if api_key_input and api_key_input != bot.api_key:
        bot.set_api_key(api_key_input)
        st.session_state["bot"] = bot
        st.success("API Key atualizada.")

    if "history" not in st.session_state:
        st.session_state["history"] = []

    user_input = st.text_input("Digite sua pergunta:", key="user_input")

    if st.button("Enviar", key="send_button"):
        if not bot.api_key:
            st.error("Por favor, informe sua API Key antes de enviar a mensagem.")
        elif not user_input.strip():
            st.warning("Digite uma pergunta para enviar.")
        else:
            resposta = bot.ask_chatgpt(user_input)
            st.session_state["history"].append(("Você", user_input))
            st.session_state["history"].append(("ChatGPT", resposta))
            st.session_state["bot"] = bot

    for speaker, msg in st.session_state.get("history", []):
        if speaker == "Você":
            st.markdown(f"**{speaker}:** {msg}")
        else:
            st.markdown(f"**{speaker}:** {msg}")

    if st.button("Limpar chat e contexto", key="clear_button"):
        st.session_state["history"] = []
        bot.load_file_context()
        st.session_state["bot"] = bot
        st.success("Chat e contexto limpos. Faça uma nova pergunta para continuar.")

# ===================== Main =====================
def main():
    if "bot" not in st.session_state:
        st.session_state["bot"] = Bot()

    bot = st.session_state["bot"]
    render_interface(bot)

if __name__ == "__main__":
    main()

# main.py
import streamlit as st
import fitz  # PyMuPDF
import os
from openai import OpenAI

# -------------------------
# Classe Bot
# -------------------------
class Bot:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.client = None
        self.file_context = None

        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            self.client = OpenAI()  # sem passar api_key

    def read_pdf(self, file_path):
        text = ""
        try:
            with fitz.open(file_path) as pdf:
                for page in pdf:
                    text += page.get_text()
            return text
        except Exception as e:
            return f"[Erro ao ler PDF: {e}]"

    def load_file_context(self, uploaded_files):
        context = ""
        try:
            for uploaded_file in uploaded_files:
                filename = uploaded_file.name

                if filename.lower().endswith(".txt"):
                    content = uploaded_file.read().decode("utf-8")
                    context += f"\n\n--- {filename} ---\n{content}"

                elif filename.lower().endswith(".pdf"):
                    temp_path = f"/tmp/{filename}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.read())
                    context += f"\n\n--- {filename} ---\n{self.read_pdf(temp_path)}"

            if context:
                self.file_context = context
                return "📂 Arquivos carregados com sucesso."
            else:
                return "⚠️ Nenhum arquivo válido carregado."

        except Exception as e:
            return f"Erro ao carregar arquivos: {str(e)}"

    def ask_chatgpt(self, user_input):
        if not self.api_key:
            return "⚠️ API Key não definida. Configure primeiro em '⚙️ Configurações'."

        if not user_input.strip():
            return "⚠️ Por favor, digite algo."

        try:
            if not self.client:
                self.client = OpenAI()  # instância via variável de ambiente

            messages = []
            if self.file_context:
                messages.append({"role": "system", "content": f"Use o seguinte contexto: {self.file_context}"})
            messages.append({"role": "user", "content": user_input})

            response = self.client.chat.completions.create(
                model="o4-mini-2025-04-16",
                messages=messages
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            return f"Erro: {str(e)}"

    def set_api_key(self, api_key):
        self.api_key = api_key
        os.environ["OPENAI_API_KEY"] = api_key
        self.client = OpenAI()  # instância via variável de ambiente
        return "🔑 API Key atualizada com sucesso."


# -------------------------
# Interface Streamlit
# -------------------------
def main():
    st.set_page_config(page_title="ChatGPT Bot", layout="wide")
    st.title("🤖 ChatGPT Bot")

    # Estado global
    if "bot" not in st.session_state:
        st.session_state.bot = Bot()
    if "messages" not in st.session_state:
        st.session_state.messages = []

    bot = st.session_state.bot

    # Configurações
    with st.expander("⚙️ Configurações"):
        api_key = st.text_input("Coloque sua API Key:", type="password")
        if st.button("Atualizar a API"):
            if api_key:
                result = bot.set_api_key(api_key)
                st.success(result)
            else:
                st.warning("Digite uma API Key válida.")

        uploaded_files = st.file_uploader(
            "Faça upload de arquivos .txt ou .pdf para contexto",
            type=["txt", "pdf"],
            accept_multiple_files=True
        )
        if uploaded_files:
            result = bot.load_file_context(uploaded_files)
            st.info(result)

        if st.button("Limpar contexto"):
            bot.file_context = None
            st.success("Contexto limpo com sucesso.")

    # Histórico do chat
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"**Você:** {msg['content']}")
        else:
            st.markdown(f"**ChatGPT:** {msg['content']}")

    # Entrada de texto
    user_input = st.text_input("Digite sua mensagem:")
    if st.button("Enviar"):
        if user_input.strip():
            st.session_state.messages.append({"role": "user", "content": user_input})
            response = bot.ask_chatgpt(user_input)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.experimental_rerun()
        else:
            st.warning("Digite algo antes de enviar.")


if __name__ == "__main__":
    main()

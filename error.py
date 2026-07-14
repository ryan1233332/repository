import streamlit as st
import requests

# --- CONFIGURAÇÃO E ESTADO ---
BOT_API_URL = "http://localhost:8080"
st.set_page_config(page_title="Slangify AI", layout="centered")

# Inicialização de segurança (para não dar aquele erro de atributo)
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "usuario_atual" not in st.session_state: st.session_state.usuario_atual = ""
if "texto_usuario" not in st.session_state: st.session_state.texto_usuario = ""
if "sugestoes_atuais" not in st.session_state: st.session_state.sugestoes_atuais = []

# --- FUNÇÕES DE LÓGICA ---
def buscar_sugestoes_relacionadas(texto):
    if not texto: return []
    # Aqui entra a lógica da sua IA ou busca que você estava usando
    return [f"Sugestão top para: {texto}", f"Outra ideia: {texto}"]

def ao_mudar_texto():
    # O callback que estava dando erro agora funciona porque inicializamos tudo acima
    st.session_state.sugestoes_atuais = buscar_sugestoes_relacionadas(st.session_state.texto_usuario)

# --- TELA DE LOGIN/SOLICITAÇÃO ---
if not st.session_state.authenticated:
    st.title("⚡ Slangify AI - Acesso")
    user = st.text_input("Nome de usuário (Discord):")
    motivo = st.text_area("Por que você quer acesso?")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Solicitar Acesso"):
            if user:
                try:
                    requests.post(f"{BOT_API_URL}/request", json={"username": user, "motivo": motivo, "ip": "user_pc"})
                    st.session_state.usuario_atual = user
                    st.success("Solicitação enviada ao Discord!")
                except:
                    st.error("Erro: O bot não está rodando.")
    with col2:
        if st.button("Verificar Aprovação"):
            try:
                res = requests.get(f"{BOT_API_URL}/check", params={"user": st.session_state.usuario_atual})
                if res.json().get("aprovado"):
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.warning("Aguardando aprovação...")
            except:
                st.error("Erro ao conectar no bot.")

# --- TELA PRINCIPAL (APÓS LOGIN) ---
else:
    st.title("🚀 Slangify AI Liberado")
    st.write(f"Bem-vindo, {st.session_state.usuario_atual}!")
    
    # Campo que usa o callback corrigido
    st.text_input("Digite o tema:", key="texto_usuario", on_change=ao_mudar_texto)
    
    if st.session_state.sugestoes_atuais:
        st.subheader("Sugestões encontradas:")
        for sug in st.session_state.sugestoes_atuais:
            st.write(f"- {sug}")
            
    if st.button("Sair"):
        st.session_state.authenticated = False
        st.rerun()
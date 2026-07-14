import os
import random
import requests
import streamlit as st
import time
from datetime import datetime
from openai import OpenAI

# Configuração da página premium
st.set_page_config(
    page_title="Slangify AI", 
    page_icon="⚡", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Endereço local onde o bot.py está rodando a API
BOT_API_URL = "http://localhost:8080" 

# Inicializar estados da sessão
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "solicitacao_enviada" not in st.session_state:
    st.session_state.solicitacao_enviada = False

if "usuario_atual" not in st.session_state:
    st.session_state.usuario_atual = ""

if "input_text" not in st.session_state:
    st.session_state.input_text = ""


# Função para capturar o IP do usuário de forma segura
def obter_ip_cliente():
    try:
        headers = st.context.headers
        if "X-Forwarded-For" in headers:
            return headers["X-Forwarded-For"].split(",")[0].strip()
        elif "X-Real-IP" in headers:
            return headers["X-Real-IP"]
        return "Não detectado (Ambiente Local)"
    except Exception:
        return "Não detectado"


# Função para enviar a solicitação para a API do bot.py
def enviar_solicitacao_para_bot(discord_user, motivo):
    ip_usuario = obter_ip_cliente()
    
    payload = {
        "username": discord_user.strip(),
        "motivo": motivo.strip() if motivo.strip() else "Nenhum motivo informado",
        "ip": ip_usuario
    }
    
    try:
        # Envia a requisição para a API local do bot.py
        response = requests.post(f"{BOT_API_URL}/request", json=payload, timeout=4)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Não foi possível conectar ao bot.py. Certifique-se de que ele está rodando na porta 8080. Erro: {e}")
        return False


# Função para verificar com o bot.py se o usuário foi aceito de verdade
def verificar_se_foi_aprovado(discord_user):
    try:
        response = requests.get(f"{BOT_API_URL}/check", params={"user": discord_user}, timeout=2)
        if response.status_code == 200:
            # Retorna o status real direto da memória do bot
            dados = response.json()
            return dados.get("aprovado", False)
    except Exception:
        pass 
    return False


# ==========================================================
# 1. TELA DE LOGIN / AGUARDANDO APROVAÇÃO (ESTILIZADA E ANIMADA)
# ==========================================================
if not st.session_state.authenticated:
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        div[data-testid="stDecoration"] {display: none;}
        
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stMainBlockContainer"] {
            background-color: #030303 !important;
            background-image: none !important;
        }
        
        .block-container {
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            align-items: center !important;
            min-height: 90vh !important;
            padding: 0 1.5rem !important;
        }

        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(15px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes subtleColorShift {
            0% { color: #ffffff; }
            50% { color: #a855f7; }
            100% { color: #ffffff; }
        }

        .slangify-nav {
            animation: fadeInUp 0.6s ease-out;
            text-align: center;
            margin-bottom: 24px;
        }
        .slangify-logo {
            font-weight: 800;
            font-size: 32px;
            letter-spacing: -1.5px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            animation: subtleColorShift 6s ease-in-out infinite;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            max-width: 450px !important;
            width: 100% !important;
            background: #09090b !important;
            border: 1px solid #1c1c1e !important;
            border-radius: 16px !important;
            padding: 30px !important;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.7) !important;
            animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1);
            box-sizing: border-box !important;
            margin: 0 auto !important;
        }

        div[data-testid="stVerticalBlock"] {
            gap: 12px !important;
        }

        .login-title {
            color: #FFFFFF;
            font-size: 26px;
            font-weight: 700;
            margin-bottom: 4px;
            letter-spacing: -0.5px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        .login-subtitle {
            color: #71717A;
            font-size: 13.5px;
            line-height: 1.5;
            margin-bottom: 16px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }

        .field-label {
            color: #A1A1AA;
            font-size: 12px;
            font-weight: 600;
            margin-top: 8px;
            margin-bottom: 6px;
            display: block;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }

        div[data-testid="stTextInput"] input {
            background-color: #121214 !important;
            color: #FFFFFF !important;
            border: 1px solid #27272A !important;
            border-radius: 10px !important;
            padding: 12px 14px !important;
            font-size: 14px !important;
            transition: all 0.25s ease !important;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.4);
            width: 100% !important;
        }
        div[data-testid="stTextInput"] input:focus {
            border-color: #a855f7 !important;
            box-shadow: 0 0 10px rgba(168, 85, 247, 0.2) !important;
        }

        div[data-testid="stButton"] {
            width: 100% !important;
            margin-top: 10px !important;
        }
        div[data-testid="stButton"] button {
            width: 100% !important;
            background-color: #a855f7 !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 12px 20px !important;
            font-size: 14px !important;
            font-weight: 600 !important;
            cursor: pointer !important;
            transition: all 0.2s ease-in-out !important;
            display: block !important;
            box-shadow: 0 4px 12px rgba(168, 85, 247, 0.2) !important;
        }
        div[data-testid="stButton"] button:hover {
            background-color: #b566ff !important;
            color: #ffffff !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 15px rgba(168, 85, 247, 0.3) !important;
        }
        div[data-testid="stButton"] button:active {
            transform: translateY(1px) !important;
        }

        .waiting-box {
            text-align: center;
            padding: 10px 0;
        }

        .login-footer {
            text-align: center;
            margin-top: 24px;
            font-size: 12px;
            color: #52525b;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        .login-footer a {
            color: #a855f7;
            text-decoration: none;
            font-weight: 600;
            transition: color 0.2s ease;
        }
        .login-footer a:hover {
            color: #c084fc;
            text-decoration: underline;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="slangify-nav">
            <div class="slangify-logo">Slangify AI</div>
        </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        if not st.session_state.solicitacao_enviada:
            st.markdown('<div class="login-title">Request Access</div>', unsafe_allow_html=True)
            st.markdown('<div class="login-subtitle">Submit your Discord username below to request instant activation for Slangify AI.</div>', unsafe_allow_html=True)
            
            st.markdown('<span class="field-label">Your Discord Username</span>', unsafe_allow_html=True)
            discord_user = st.text_input("Discord User", placeholder="e.g., ryanflw", label_visibility="collapsed", key="req_discord")
            
            st.markdown('<span class="field-label">Why do you want access? (Optional)</span>', unsafe_allow_html=True)
            motivo = st.text_input("Motivo", placeholder="Tell us briefly...", label_visibility="collapsed", key="req_motivo")
            
            if st.button("Request Access"):
                if discord_user.strip() == "":
                    st.error("Please provide your Discord username.")
                else:
                    with st.spinner("Processing request..."):
                        sucesso = enviar_solicitacao_para_bot(discord_user, motivo)
                        if sucesso:
                            st.session_state.usuario_atual = discord_user.lower().strip()
                            st.session_state.solicitacao_enviada = True
                            st.rerun()
                        else:
                            st.error("Certifique-se de que o `bot.py` está aberto e rodando!")
        else:
            st.markdown("""
                <div class="waiting-box">
                    <div class="login-title" style="color: #a855f7;">Awaiting Approval...</div>
                    <div class="login-subtitle" style="font-size: 14px; line-height: 1.6; margin-top: 15px;">
                        Request successfully sent for <br><b style="color: #ffffff; font-size: 16px;">@""" + st.session_state.usuario_atual + """</b>.<br><br>
                        Please wait. Once an admin clicks <b>Aprovar Acesso</b> on Discord, this page will unlock automatically.
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            with st.spinner("Checking approval status..."):
                time.sleep(3)
                if verificar_se_foi_aprovado(st.session_state.usuario_atual):
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.rerun()

    st.markdown("""
        <div class="login-footer">
            Need immediate help? <a href="https://discord.com/users/1355965493277888524" target="_blank">Contact Admin</a>
        </div>
    """, unsafe_allow_html=True)


# ==========================================================
# 2. SITE PRINCIPAL DO SLANGIFY AI (ESTILIZADO E ALINHADO)
# ==========================================================
else:
    # Banco de ideias rápidas para rotacionar/filtrar
    BANCO_DE_IDEIAS = [
        ("📸 Amei a foto", "Amei sua foto de perfil, ficou muito boa"),
        ("👻 Você sumiu", "Você sumiu, não fala mais comigo"),
        ("🔥 Mentira, sério?", "Mentira, sério mesmo isso?"),
        ("👀 Vi seu story", "Vi seu story ontem e achei muito engraçado"),
        ("🍿 Bora assistir", "Bora assistir um filme no fim de semana?"),
        ("💡 Que ideia boa", "Caramba, essa ideia que você teve foi incrível"),
        ("🎉 Parabéns!", "Parabéns pelo seu aniversário! Tudo de bom sempre"),
        ("😴 Estou com sono", "Estou morrendo de sono, vou dormir logo"),
        ("🍕 Com fome", "Queria comer uma pizza gigante agora"),
        ("🎸 Curti o som", "Amei essa música que você compartilhou"),
        ("✈️ Quero viajar", "Não vejo a hora de viajar de novo"),
        ("☕ Café agora", "Preciso de um café bem forte pra acordar")
    ]

    def buscar_sugestoes_relacionadas(texto_usuario):
        if not texto_usuario.strip():
            return random.sample(BANCO_DE_IDEIAS, 3)
        
        texto_usuario_lower = texto_usuario.lower()
        palavras_chave_contexto = {
            "foto": ["foto", "perfil", "story", "insta", "visto", "olha", "linda"],
            "sumiu": ["sumiu", "visto", "falou", "mensagem", "vácuo", "responder"],
            "comida": ["pizza", "comer", "fome", "jantar", "café", "almoço", "doce"],
            "entretenimento": ["filme", "assistir", "netflix", "série", "música", "som", "guitarra", "show"],
            "viagem": ["viajar", "férias", "avião", "praia", "role", "sair"],
            "sono": ["sono", "dormir", "cansado", "noite", "cama"],
            "ideia": ["ideia", "projeto", "trabalho", "pensando", "criativo"]
        }
        
        categoria_ativa = None
        for categoria, palavras in palavras_chave_contexto.items():
            if any(p in texto_usuario_lower for p in palavras):
                categoria_ativa = categoria
                break
                
        sugestoes_filtradas = []
        if categoria_ativa:
            if categoria_ativa == "foto":
                sugestoes_filtradas = [i for i in BANCO_DE_IDEIAS if "foto" in i[1].lower() or "story" in i[1].lower()]
            elif categoria_ativa == "sumiu":
                sugestoes_filtradas = [i for i in BANCO_DE_IDEIAS if "sumiu" in i[1].lower()]
            elif categoria_ativa == "comida":
                sugestoes_filtradas = [i for i in BANCO_DE_IDEIAS if "pizza" in i[1].lower() or "café" in i[1].lower()]
            elif categoria_ativa == "entretenimento":
                sugestoes_filtradas = [i for i in BANCO_DE_IDEIAS if "filme" in i[1].lower() or "música" in i[1].lower()]
            elif categoria_ativa == "sono":
                sugestoes_filtradas = [i for i in BANCO_DE_IDEIAS if "sono" in i[1].lower() or "dormir" in i[1].lower()]
            elif categoria_ativa == "ideia":
                sugestoes_filtradas = [i for i in BANCO_DE_IDEIAS if "ideia" in i[1].lower()]
                
        outras_opcoes = [i for i in BANCO_DE_IDEIAS if i not in sugestoes_filtradas]
        sugestoes_finais = (sugestoes_filtradas + random.sample(outras_opcoes, len(outras_opcoes)))[:3]
        return sugestoes_finais

    if "sugestoes_atuais" not in st.session_state:
        st.session_state.sugestoes_atuais = buscar_sugestoes_relacionadas("")

    def ao_mudar_texto():
        st.session_state.sugestoes_atuais = buscar_sugestoes_relacionadas(st.session_state.texto_usuario)

    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        .stApp {
            background-color: #030303 !important;
            background-image: none !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        .block-container {
            max-width: 650px !important;
            padding: 3rem 1.5rem !important;
            margin: 0 auto !important;
            display: block !important;
        }
        
        .header-container {
            text-align: center;
            margin-top: 20px;
            margin-bottom: 25px;
            animation: fadeInUp 0.6s ease-out;
        }
        .brand-title {
            color: #ffffff;
            font-size: 42px;
            font-weight: 800;
            letter-spacing: -1.5px;
            margin-bottom: 6px;
            animation: subtleColorShift 6s ease-in-out infinite;
        }
        .brand-subtitle {
            color: #52525b;
            font-size: 13px;
            letter-spacing: 1px;
            font-weight: 600;
            text-transform: uppercase;
            margin-bottom: 20px;
        }

        .discord-btn-container {
            display: flex;
            justify-content: center;
            margin-bottom: 35px;
            animation: fadeInUp 0.7s ease-out;
        }
        .discord-btn {
            background-color: #5865F2;
            color: #FFFFFF !important;
            border: none;
            border-radius: 12px;
            padding: 10px 20px;
            font-size: 13px;
            font-weight: 600;
            text-decoration: none !important;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.25s ease;
            box-shadow: 0 4px 20px rgba(88, 101, 242, 0.15);
        }
        .discord-btn:hover {
            background-color: #4752C4;
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(88, 101, 242, 0.3);
        }

        .stTextInput input {
            background-color: #0c0c0e !important;
            color: #FFFFFF !important;
            border: 1px solid #1F1F23 !important;
            border-radius: 14px !important;
            padding: 16px 20px !important;
            font-size: 15px !important;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5) !important;
        }
        .stTextInput input:focus {
            border-color: #a855f7 !important;
            box-shadow: 0 0 15px rgba(168, 85, 247, 0.15) !important;
        }
        
        div.stButton > button {
            background-color: #0c0c0e !important;
            color: #71717a !important;
            border: 1px solid #1f1f23 !important;
            border-radius: 12px !important;
            padding: 10px 14px !important;
            font-size: 13px !important;
            transition: all 0.2s ease !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            width: 100% !important;
            margin-top: 0px !important;
        }
        div.stButton > button:hover {
            color: #FFFFFF !important;
            border-color: #a855f7 !important;
            background-color: #121016 !important;
            transform: translateY(-1px);
        }

        .output-card {
            background: linear-gradient(145deg, #09090b 0%, #030304 100%);
            border: 1px solid #1f1f23;
            border-radius: 16px;
            padding: 24px;
            margin-top: 30px;
            box-shadow: 0 15px 40px rgba(0,0,0,0.6);
            animation: fadeInUp 0.5s cubic-bezier(0.16, 1, 0.3, 1);
            transition: border-color 0.4s ease;
        }
        .output-card:hover {
            border-color: #a855f7;
        }
        .output-header {
            color: #a855f7;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 12px;
        }
        .output-text {
            color: #FFFFFF;
            font-size: 18px;
            font-weight: 500;
            line-height: 1.6;
            letter-spacing: -0.2px;
        }
        </style>
    """, unsafe_allow_html=True)

    client = OpenAI(
        api_key="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",
        base_url="https://openrouter.ai/api/v1",
        max_retries=0
    )

    def tradutor_openrouter(texto_pt):
        system_instruction = (
            "You are a young American girl typing naturally on her phone, texting or DMing a guy. "
            "Your task is to translate Portuguese into how a real girl actually texts—using real human emotion, modern texting style, and casual abbreviations. "
            "Do NOT just swap words for cringey slang. Make it flow like a real iMessage or Instagram DM. "
            "Use lowercase only, and feel free to use standard punctuation like periods, commas, or question marks where it fits naturally. "
            "Include natural text elongations (like 'sooo', 'omg', 'lmao', 'ngl', 'rn') when appropriate to sound organic. "
            "Deliver ONLY the translation text without any notes."
            "\n\nExamples of the required human/girl tone:"
            "\nInput: Amei sua foto de perfil"
            "\nOutput: love your pfp ngl."
            "\nInput: Que foto linda, amei"
            "\nOutput: omg this pic is actually sooo cute."
            "\nInput: Você sumiu, não fala mais comigo"
            "\nOutput: u lowkey ghosted me rn smh."
            "\nInput: Me chama no direct depois"
            "\nOutput: hit my dms later."
            "\nInput: Mentira, sério?"
            "\nOutput: wait no way fr??"
        )

        try:
            response = client.chat.completions.create(
                model="openrouter/auto",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": f"Translate this: {texto_pt}"}
                ],
                temperature=0.85,
            )
            resultado = response.choices[0].message.content.strip()
            resultado = resultado.lower().replace("'", "").replace("’", "")
            return resultado
        except Exception as e:
            return f"erro de conexão: {e}"

    st.markdown("""
        <div class='header-container'>
            <div class='brand-title'>Slangify AI</div>
            <div class='brand-subtitle'>by:ryanflw</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="discord-btn-container">
            <a href="https://discord.com/users/1355965493277888524" target="_blank" class="discord-btn">
                <svg width="18" height="18" viewBox="0 0 127.14 96.36" fill="currentColor">
                    <path d="M107.7,8.07A105.15,105.15,0,0,0,77.26,0a77.19,77.19,0,0,0-3.3,6.83A96.67,96.67,0,0,0,53.22,6.83,77.19,77.19,0,0,0,49.88,0,105.15,105.15,0,0,0,19.44,8.07C3.66,31.58-1.86,54.65,1,77.53A105.73,105.73,0,0,0,32,96.36a77.7,77.7,0,0,0,6.63-10.85,68.43,68.43,0,0,1-10.5-5c.88-.65,1.72-1.34,2.53-2a75.58,75.58,0,0,0,73,0c.81.68,1.65,1.37,2.53,2a68.43,68.43,0,0,1-10.5,5,77.7,77.7,0,0,0,6.63,10.85,105.73,105.73,0,0,0,31.54-18.83C129.87,54.65,124.35,31.58,107.7,8.07ZM42.45,65.69C36.18,65.69,31,60,31,53S36.18,40.36,42.45,40.36,53.83,46,53.83,53,48.72,65.69,42.45,65.69Zm42.24,0C78.41,65.69,73.24,60,73.24,53S78.41,40.36,84.69,40.36,96.07,46,96.07,53,91,65.69,84.69,65.69Z"/>
                </svg>
                Add on Discord
            </a>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<p style='color: #52525B; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px;'>Ideias rápidas recomendadas:</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    def set_input(text):
        st.session_state.input_text = text
        st.session_state.sugestoes_atuais = buscar_sugestoes_relacionadas(text)

    sugestoes = st.session_state.sugestoes_atuais

    with col1:
        if st.button(sugestoes[0][0], use_container_width=True):
            set_input(sugestoes[0][1])
            st.rerun()
    with col2:
        if st.button(sugestoes[1][0], use_container_width=True):
            set_input(sugestoes[1][1])
            st.rerun()
    with col3:
        if st.button(sugestoes[2][0], use_container_width=True):
            set_input(sugestoes[2][1])
            st.rerun()
            
    entrada = st.text_input(
        "INPUT_FIELD", 
        value=st.session_state.input_text,
        placeholder="Digite algo em português e aperte Enter...",
        label_visibility="collapsed",
        key="texto_usuario",
        on_change=ao_mudar_texto
    )

    if entrada != st.session_state.input_text:
        st.session_state.input_text = entrada
        
    if st.session_state.input_text.strip():
        with st.spinner("Translating to slang..."):
            traducao = tradutor_openrouter(st.session_state.input_text)
        
        st.markdown(f"""
            <div class="output-card">
                <div class="output-header">Como ela digitaria:</div>
                <div class="output-text">{traducao}</div>
            </div>
        """, unsafe_allow_html=True)
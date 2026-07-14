import discord
import os  # Essencial para ler a variável de ambiente
from discord.ext import commands
from discord.ui import Button, View
from aiohttp import web
import aiohttp
import asyncio
from datetime import datetime

# --- CONFIGURAÇÕES DO SEU BOT ---
# O token não é mais escrito aqui. Ele é lido do Railway.
TOKEN = os.getenv("DISCORD_TOKEN") 
CHANNEL_ID = 526677200793895046

# --- WEBHOOK EXCLUSIVO PARA LOGS ---
LOG_WEBHOOK_URL = "https://discord.com/api/webhooks/1526690019534966906/mvQ772xJCUSg_avc0IPajSaz4_w81RUe-1UtwYKD8FI2Vh8xkwQLC8wFNu7dsGKb7CmH"

# Dicionário temporário para guardar o status dos usuários nesta sessão
solicitacoes = {}

intents = discord.Intents.default()
intents.message_content = True


# Criamos uma subclasse para gerenciar o ciclo de vida do Bot de forma moderna
class SlangifyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.web_runner = None

    async def setup_hook(self):
        # Iniciamos o servidor Web de forma limpa no ciclo do setup
        app = web.Application()
        app.router.add_post("/request", handle_request_access)
        app.router.add_get("/check", handle_check_status)
        
        self.web_runner = web.AppRunner(app)
        await self.web_runner.setup()
        site = web.TCPSite(self.web_runner, "localhost", 8080)
        await site.start()
        print("⚡ API do Bot rodando em http://localhost:8080")

    async def close(self):
        # Cleanup do servidor ao desligar o bo
        if self.web_runner:
            await self.web_runner.cleanup()
        await super().close()


bot = SlangifyBot()


# ---------------------------------------------------------
# FUNÇÃO DE LOG CORRIGIDA E ADAPTADA
# ---------------------------------------------------------
async def enviar_log(titulo, descricao, cor=8421504, campos=None):
    if not LOG_WEBHOOK_URL or "SUA_URL" in LOG_WEBHOOK_URL:
        return
        
    payload = {
        "username": "Slangify AI Auditor",
        "avatar_url": "https://i.imgur.com/8QpYh6U.png",
        "embeds": [
            {
                "title": titulo,
                "description": descricao,
                "color": cor,
                "fields": campos or [],
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "footer": {"text": "Sistema de Logs • Slangify AI"}
            }
        ]
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(LOG_WEBHOOK_URL, json=payload) as response:
                if response.status not in [200, 204]:
                    texto_erro = await response.text()
                    print(f"[LOG ERROR] Webhook retornou status {response.status}: {texto_erro}")
    except Exception as e:
        print(f"[LOG ERROR] Erro ao conectar com o webhook: {e}")


# ---------------------------------------------------------
# CLASSE DOS BOTÕES DO DISCORD
# ---------------------------------------------------------
class AprovacaoView(View):
    def __init__(self, username: str, ip: str):
        super().__init__(timeout=None)
        self.username = username.lower().strip()
        self.ip = ip

    @discord.ui.button(label="Aprovar Acesso", style=discord.ButtonStyle.green, custom_id="btn_aprovar", emoji="✅")
    async def aprovar_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        solicitacoes[self.username] = "aprovado"
        
        for item in self.children:
            item.disabled = True
            
        await interaction.response.edit_message(
            content=f"✅ **Acesso APROVADO** para `@{self.username}` por {interaction.user.mention}.",
            view=self,
            embed=None
        )
        
        # Envia Log de Aprovação
        await enviar_log(
            titulo="🟢 Acesso Aprovado",
            descricao=f"O usuário `@{self.username}` foi liberado para usar o Slangify AI.",
            cor=3066993, # Verde
            campos=[
                {"name": "👤 Usuário", "value": f"`@{self.username}`", "inline": True},
                {"name": "⚙️ Autorizado por", "value": f"{interaction.user.name} ({interaction.user.mention})", "inline": True},
                {"name": "🌐 IP do Usuário", "value": f"`{self.ip}`", "inline": False}
            ]
        )

    @discord.ui.button(label="Recusar Acesso", style=discord.ButtonStyle.red, custom_id="btn_recusar", emoji="❌")
    async def recusar_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        solicitacoes[self.username] = "recusado"
        
        for item in self.children:
            item.disabled = True
            
        await interaction.response.edit_message(
            content=f"❌ **Acesso RECUSADO** para `@{self.username}` por {interaction.user.mention}.",
            view=self,
            embed=None
        )
        
        # Envia Log de Recusa
        await enviar_log(
            titulo="🔴 Acesso Recusado",
            descricao=f"A solicitação de `@{self.username}` foi rejeitada.",
            cor=15158332, # Vermelho
            campos=[
                {"name": "👤 Usuário", "value": f"`@{self.username}`", "inline": True},
                {"name": "⚙️ Recusado por", "value": f"{interaction.user.name} ({interaction.user.mention})", "inline": True},
                {"name": "🌐 IP do Usuário", "value": f"`{self.ip}`", "inline": False}
            ]
        )


# ---------------------------------------------------------
# ROTAS DA API
# ---------------------------------------------------------
async def handle_request_access(request):
    try:
        data = await request.json()
        username = data.get("username", "").lower().strip()
        motivo = data.get("motivo", "*Não informado*")
        ip = data.get("ip", "Desconhecido")
        
        if not username:
            return web.json_response({"success": False, "error": "Username ausente"}, status=400)

        solicitacoes[username] = "pendente"

        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="⚡ Nova Solicitação de Acesso",
                description="Um usuário solicitou acesso ao **Slangify AI**.",
                color=discord.Color.purple()
            )
            embed.add_field(name="👤 Usuário", value=f"`@{username}`", inline=True)
            embed.add_field(name="🌐 IP", value=f"`{ip}`", inline=True)
            embed.add_field(name="📝 Motivo", value=motivo, inline=False)
            embed.set_footer(text="Aprove ou recuse usando os botões abaixo")

            view = AprovacaoView(username, ip)
            bot.loop.create_task(channel.send(embed=embed, view=view))
            
            # Envia Log de Nova Solicitação Criada
            await enviar_log(
                titulo="📝 Nova Solicitação Recebida",
                descricao=f"O usuário `@{username}` solicitou liberação de acesso.",
                cor=10181046, # Roxo
                campos=[
                    {"name": "👤 Usuário", "value": f"`@{username}`", "inline": True},
                    {"name": "🌐 IP", "value": f"`{ip}`", "inline": True},
                    {"name": "📝 Motivo", "value": motivo, "inline": False}
                ]
            )
            
            return web.json_response({"success": True})
        else:
            erro_msg = f"Canal {CHANNEL_ID} não encontrado pelo Bot."
            print(erro_msg)
            await enviar_log("⚠️ Erro de Inicialização", erro_msg, cor=15158332)
            return web.json_response({"success": False, "error": "Canal não encontrado"}, status=500)
            
    except Exception as e:
        erro_msg = f"Erro ao processar requisição de acesso: {str(e)}"
        print(erro_msg)
        await enviar_log("⚠️ Erro Interno do Bot", erro_msg, cor=15158332)
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def handle_check_status(request):
    username = request.query.get("user", "").lower().strip()
    status = solicitacoes.get(username, "nao_solicitado")
    
    esta_aprovado = (status == "aprovado")
    
    if esta_aprovado:
        solicitacoes[username] = "logado" 
        await enviar_log(
            titulo="🚀 Usuário Entrou no Sistema",
            descricao=f"O usuário `@{username}` acabou de carregar a tela principal do Slangify AI com sucesso!",
            cor=3447003 # Azul
        )

    return web.json_response({"aprovado": (esta_aprovado or status == "logado"), "status": status})


# ---------------------------------------------------------
# EVENTOS DO BOT
# ---------------------------------------------------------
@bot.event
async def on_ready():
    print(f"✅ Bot logado como {bot.user.name}!")
    # Dispara a log de inicialização apenas após o bot estar conectado e estável
    await enviar_log(
        titulo="⚙️ Sistema Iniciado", 
        descricao="A API local do bot e o sistema de escuta foram iniciados com sucesso na porta 8080.", 
        cor=3447003
    )


# Iniciar o Bot
if __name__ == "__main__":
    bot.run(TOKEN)

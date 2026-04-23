import discord
from discord.ext import commands
from src.database.db import get_user, create_or_update_user
from src.data.data_manager import DataManager
import logging

logger = logging.getLogger("DiscordCommands")

class TradingCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="start")
    async def start(self, ctx):
        embed = discord.Embed(
            title="👋 Bem-vindo ao Bot Trading Pro AI",
            description=(
                "O sistema de inteligência artificial mais avançado para sinais na B3 (Mini Índice e Mini Dólar).\n\n"
                "📈 **O que eu faço?**\n"
                "Analiso volume, price action e indicadores técnicos usando XGBoost para prever a próxima tendência."
            ),
            color=discord.Color.blue()
        )
        embed.add_field(name="📌 Comandos", value="`!analisar` - Gerar sinal\n`!vip` - Adquirir acesso\n`!ajuda` - Guia completo", inline=False)
        
        # In Discord, we use buttons via View, but for now let's keep it simple with text/embed
        await ctx.send(embed=embed)

    @commands.command(name="info")
    async def info(self, ctx):
        embed = discord.Embed(
            title="🤖 Sobre a Inteligência Artificial",
            description=(
                "O Bot utiliza um modelo **XGBoost (Extreme Gradient Boosting)** treinado com dados históricos da B3.\n\n"
                "🔍 **Fatores de Decisão:**\n"
                "• **Volume:** Analisa a força do movimento.\n"
                "• **Price Action:** Detecta topos e fundos.\n"
                "• **Tendência:** Médias Móveis Exponenciais (9/21).\n"
                "• **Volatilidade:** Bandas de Bollinger."
            ),
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command(name="suporte")
    async def suporte(self, ctx):
        embed = discord.Embed(
            title="🛠️ Suporte Técnico",
            description=(
                "Está com problemas ou tem dúvidas?\n"
                "Fale com nossa equipe:\n\n"
                "👉 Discord: @seu_suporte_aqui\n"
                "👉 Horário: Segunda a Sexta (09h-18h)"
            ),
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

    @commands.command(name="ajuda")
    async def ajuda(self, ctx):
        embed = discord.Embed(
            title="📖 Guia de Uso",
            description=(
                "1️⃣ **Análise:** Use `!analisar WDO` ou `!analisar WIN`.\n"
                "2️⃣ **VIP:** Libera sinais ilimitados. Use `!vip` para assinar.\n"
                "3️⃣ **Gerenciamento:** NUNCA opere sem Stop Loss."
            ),
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name="status")
    async def status(self, ctx):
        user_id = str(ctx.author.id)
        user = get_user(user_id)
        status = "💎 VIP" if user and user.is_vip else "🆓 Gratuito"
        
        embed = discord.Embed(title="👤 Status da Conta", color=discord.Color.light_grey())
        embed.add_field(name="Usuário", value=ctx.author.name, inline=True)
        embed.add_field(name="Plano", value=status, inline=True)
        
        if not user or not user.is_vip:
            embed.set_footer(text="⚠️ Plano limitado. Use !vip para assinar.")
            
        await ctx.send(embed=embed)

    @commands.command(name="vip")
    async def vip(self, ctx):
        user_id = str(ctx.author.id)
        payment_url = self.bot.pm.create_payment_link(user_id, "discord")
        
        embed = discord.Embed(
            title="💎 VANTAGENS DO ACESSO VIP",
            description=(
                "✅ Sinais ilimitados para WIN e WDO\n"
                "✅ Maior precisão (Modelos 2.0)\n"
                "✅ Acesso vitalício (Sem mensalidade)"
            ),
            color=discord.Color.gold()
        )
        embed.add_field(name="Preço", value="R$ 30,00", inline=True)
        embed.add_field(name="Pagamento", value=f"[Clique aqui para pagar via Pix/Cartão]({payment_url})", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="analisar")
    async def analisar(self, ctx, asset: str = "WDO"):
        user_id = str(ctx.author.id)
        asset = asset.upper()
        
        # Sync payment status
        is_paid = self.bot.pm.check_payment_status(f"discord_{user_id}")
        if is_paid:
            create_or_update_user(user_id, "discord", True)
        
        user = get_user(user_id)
        if not user or not user.is_vip:
            await ctx.send("❌ **Acesso Negado.** Esta função é exclusiva para membros VIP. Use `!vip` para assinar.")
            return

        status_msg = await ctx.send(f"🔄 **Analisando {asset}...** coletando dados da B3.")
        
        try:
            dm = DataManager(asset_type=asset)
            data = dm.fetch_data(period="5d", interval="5m")
            data_with_indicators = dm.add_indicators(data)
            
            self.bot.predictor.load_model()
            last_row = data_with_indicators.iloc[[-1]]
            prediction, prob = self.bot.predictor.predict_next(last_row)
            
            signal = "🟢 COMPRA" if prediction == 1 else "🔴 VENDA"
            confidence = prob if prediction == 1 else (1 - prob)
            strength = "🔥 FORTE" if confidence > 0.75 else "⚡ MODERADA"
            
            embed = discord.Embed(title="📊 ANÁLISE DE MERCADO B3", color=discord.Color.blue())
            embed.add_field(name="Ativo", value=f"`{asset}`", inline=True)
            embed.add_field(name="Sinal", value=f"**{signal}**", inline=True)
            embed.add_field(name="Força", value=strength, inline=True)
            embed.add_field(name="Confiança", value=f"`{confidence:.2%}`", inline=False)
            embed.add_field(name="Estratégia", value="XGBoost Pro V2", inline=True)
            embed.set_footer(text="⚠️ Use stop loss técnico em todas as operações.")
            
            await status_msg.edit(content=None, embed=embed)
        except Exception as e:
            logger.error(f"Erro na análise Discord: {e}")
            await status_msg.edit(content=f"❌ **Erro:** Não foi possível analisar o ativo {asset}.")

async def setup_discord_commands(bot):
    await bot.add_cog(TradingCommands(bot))

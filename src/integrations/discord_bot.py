import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from src.data.data_manager import DataManager
from src.models.predictor import TradingPredictor
from src.integrations.mercado_pago import PaymentManager
from src.database.db import get_user, create_or_update_user, init_db

load_dotenv()

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.dm = DataManager()
        self.predictor = TradingPredictor()
        self.pm = PaymentManager()
        init_db()

    async def on_ready(self):
        print(f"Discord Bot logado como {self.user}")

    @commands.command()
    async def vip(self, ctx):
        user_id = str(ctx.author.id)
        payment_url = self.pm.create_payment_link(user_id, "discord")
        
        embed = discord.Embed(
            title="💎 Acesso VIP",
            description="Garanta acesso aos sinais de alta precisão do Bot Trading Pro.",
            color=discord.Color.gold()
        )
        embed.add_field(name="Preço", value="R$ 30,00", inline=True)
        embed.add_field(name="Link de Pagamento", value=f"[Pagar Agora]({payment_url})", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command()
    async def analisar(self, ctx):
        user_id = str(ctx.author.id)
        
        # Verification logic
        is_paid = self.pm.check_payment_status(f"discord_{user_id}")
        if is_paid:
            create_or_update_user(user_id, "discord", True)
        
        user = get_user(user_id)
        if not user or not user.is_vip:
            await ctx.send("❌ Acesso Negado. Use `!vip` para assinar.")
            return

        await ctx.send("🔄 Analisando mercado...")
        
        try:
            data = self.dm.fetch_data(period="5d", interval="5m")
            data_with_indicators = self.dm.add_indicators(data)
            
            self.predictor.load_model()
            last_row = data_with_indicators.iloc[[-1]]
            prediction, prob = self.predictor.predict_next(last_row)
            
            signal = "🟢 COMPRA" if prediction == 1 else "🔴 VENDA"
            confidence = prob if prediction == 1 else (1 - prob)
            
            embed = discord.Embed(title="📊 Análise de Mercado", color=discord.Color.blue())
            embed.add_field(name="Ativo", value=self.dm.symbol, inline=True)
            embed.add_field(name="Sinal", value=f"**{signal}**", inline=True)
            embed.add_field(name="Confiança", value=f"{confidence:.2%}", inline=False)
            embed.set_footer(text="Use com gerenciamento de risco.")
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erro: {str(e)}")

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(os.getenv("DISCORD_TOKEN"))

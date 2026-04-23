import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from src.data.data_manager import DataManager
from src.models.predictor import TradingPredictor
from src.integrations.mercado_pago import PaymentManager
from src.database.db import get_user, create_or_update_user, init_db
from src.utils.logger import setup_logger

load_dotenv()
logger = setup_logger("DiscordBot")

from src.comandos.comandos_discord import setup_discord_commands

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True # Optional but helpful
        super().__init__(command_prefix="!", intents=intents)
        self.dm = DataManager()
        self.predictor = TradingPredictor()
        self.pm = PaymentManager()


    async def setup_hook(self):
        # Register external commands
        await setup_discord_commands(self)
        
        # Sync slash commands (if any are defined as app_commands)
        # Note: Cog commands can be app_commands too
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands.")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")

    async def on_ready(self):
        logger.info(f"Discord Bot logado como {self.user}")
        await self.change_presence(activity=discord.Game(name="B3 - Mini Índice/Dólar"))

if __name__ == "__main__":
    bot = DiscordBot()
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        logger.error("DISCORD_TOKEN não encontrado no ambiente.")



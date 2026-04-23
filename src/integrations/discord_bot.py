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
        super().__init__(command_prefix="!", intents=intents)
        self.dm = DataManager()
        self.predictor = TradingPredictor()
        self.pm = PaymentManager()
        init_db()

    async def setup_hook(self):
        # Register external commands
        await setup_discord_commands(self)

    async def on_ready(self):
        logger.info(f"Discord Bot logado como {self.user}")

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run(os.getenv("DISCORD_TOKEN"))


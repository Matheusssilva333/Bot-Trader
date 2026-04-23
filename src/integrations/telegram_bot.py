import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from src.data.data_manager import DataManager
from src.models.predictor import TradingPredictor
from src.integrations.mercado_pago import PaymentManager
from src.database.db import get_user, create_or_update_user, init_db
from dotenv import load_dotenv
from src.utils.logger import setup_logger

load_dotenv()
logger = setup_logger("TelegramBot")

from src.comandos.comandos_telegram import setup_telegram_commands

class TelegramBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_TOKEN")
        if not self.token:
            logger.error("TELEGRAM_TOKEN não encontrado!")
            return
        self.dm = DataManager()
        self.predictor = TradingPredictor()
        self.pm = PaymentManager()


    def run(self):
        if not self.token:
            return
            
        async def post_init(application):
            await application.bot.set_my_commands([
                ("start", "Inicia o bot"),
                ("analisar", "Gera um sinal de trading"),
                ("vip", "Adquire acesso VIP"),
                ("status", "Verifica seu plano"),
                ("ajuda", "Mostra o guia de uso"),
                ("info", "Sobre a IA"),
                ("suporte", "Suporte técnico")
            ])

        app = ApplicationBuilder().token(self.token).post_init(post_init).build()
        
        # Setup external commands
        setup_telegram_commands(app, self)
        
        logger.info("Telegram Bot is running with menu commands...")
        # stop_signals=False is REQUIRED when running in a thread
        app.run_polling(stop_signals=False)



if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()


import os
import traceback
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from src.data.data_manager import DataManager
from src.models.predictor import TradingPredictor
from src.integrations.mercado_pago import PaymentManager
from src.integrations.claude_ai import ClaudeAnalyzer
from src.database.db import get_user, create_or_update_user

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
        
        # Load model once at startup
        if self.predictor.load_model():
            logger.info("✅ ML Model loaded successfully.")
        else:
            logger.warning("⚠️ ML Model or Scaler not found. Run train_model.py first.")
            
        self.pm = PaymentManager()
        self.ai = ClaudeAnalyzer()



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

        async def on_error(update: object, context):
            logger.error("Exceção não tratada no handler do Telegram", exc_info=context.error)
            if isinstance(update, Update) and update.effective_message:
                try:
                    await update.effective_message.reply_text(
                        "⚠️ Ocorreu um erro interno. Tente de novo em instantes ou use /ajuda."
                    )
                except Exception:
                    logger.debug("Não foi possível enviar mensagem de erro ao usuário:\n%s", traceback.format_exc())

        app.add_error_handler(on_error)

        # Setup external commands
        setup_telegram_commands(app, self)

        logger.info("Telegram Bot is running with menu commands...")
        # stop_signals=False is REQUIRED when running in a thread
        app.run_polling(stop_signals=False)



if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()


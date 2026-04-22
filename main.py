import threading
import os
from src.integrations.telegram_bot import TelegramBot
from src.integrations.discord_bot import DiscordBot
from dotenv import load_dotenv

from src.utils.logger import setup_logger

load_dotenv()
logger = setup_logger("Main")

def run_telegram():
    try:
        logger.info("Iniciando Telegram Bot...")
        bot = TelegramBot()
        bot.run()
    except Exception as e:
        logger.error(f"Erro no Telegram Bot: {e}")

def run_discord():
    try:
        logger.info("Iniciando Discord Bot...")
        bot = DiscordBot()
        bot.run(os.getenv("DISCORD_TOKEN"))
    except Exception as e:
        logger.error(f"Erro no Discord Bot: {e}")

if __name__ == "__main__":
    logger.info("--- Sistema de Dashboards & Bots Trading AI ---")
    logger.info("Iniciando serviços...")

    # Verification of environment variables
    missing = []
    for var in ["TELEGRAM_TOKEN", "DISCORD_TOKEN", "MERCADO_PAGO_ACCESS_TOKEN"]:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        logger.warning(f"AVISO: As seguintes variáveis de ambiente estão faltando: {', '.join(missing)}")
        logger.warning("Por favor, preencha o arquivo .env para que os bots funcionem corretamente.")

    # Running both bots in parallel threads for local testing
    # In production, it's better to use separate containers or processes.
    t_telegram = threading.Thread(target=run_telegram)
    t_discord = threading.Thread(target=run_discord)

    t_telegram.start()
    t_discord.start()

    t_telegram.join()
    t_discord.join()

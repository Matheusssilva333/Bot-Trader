import os
import threading
from src.integrations.telegram_bot import TelegramBot
from src.database.db import init_db
from src.utils.logger import setup_logger
from flask import Flask

# Configuração de Logs
logger = setup_logger("Main")

# Servidor Flask para Health Check (Render requer um serviço web)
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot Trading Pro AI is running!", 200

def run_http_server():
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def run_telegram():
    """Mantém o polling ativo: reinicia após falhas de rede ou encerramento inesperado."""
    import time
    backoff = 5
    max_backoff = 300
    while True:
        try:
            logger.info("Iniciando Telegram Bot...")
            bot = TelegramBot()
            if not getattr(bot, "token", None):
                logger.error("TelegramBot sem token; encerrando thread do Telegram.")
                return
            bot.run()
            logger.warning("Polling do Telegram encerrou; reiniciando em %ss.", backoff)
        except Exception as e:
            logger.exception("Erro no Telegram Bot: %s", e)
            logger.info("Nova tentativa em %ss.", backoff)
        time.sleep(backoff)
        backoff = min(backoff * 2, max_backoff)

def main():
    logger.info("🚀 Iniciando Sistema Trading Pro AI (Apenas Telegram)...")

    logger.info("Inicializando banco local (SQLite)...")
    init_db()
    logger.info("✅ Banco de dados inicializado.")

    telegram_token = os.getenv("TELEGRAM_TOKEN")
    
    if not telegram_token:
        logger.error("❌ ERRO CRÍTICO: TELEGRAM_TOKEN não encontrado.")
        return

    # Inicia o Servidor HTTP para o Render em uma Thread separada
    t_http = threading.Thread(target=run_http_server, name="HTTPThread", daemon=True)
    t_http.start()
    
    # Inicia o Telegram Bot com um pequeno delay para evitar conflitos de deploy
    import time
    time.sleep(5)
    
    logger.info("✅ Iniciando conexão com o Telegram...")
    run_telegram()

if __name__ == "__main__":
    main()

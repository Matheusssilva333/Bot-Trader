import os
import threading
import logging
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
    try:
        logger.info("Iniciando Telegram Bot...")
        bot = TelegramBot()
        bot.run()
    except Exception as e:
        logger.error(f"Erro no Telegram Bot: {e}")

def main():
    logger.info("🚀 Iniciando Sistema Trading Pro AI (Apenas Telegram)...")
    
    # Inicializa o Banco de Dados com Fallback de segurança
    try:
        logger.info("Conectando ao banco de dados...")
        init_db()
        logger.info("✅ Banco de dados inicializado.")
    except Exception as e:
        logger.error(f"❌ Erro ao conectar no banco de dados principal: {e}")
        logger.warning("⚠️ Iniciando em modo de segurança com Banco Local (SQLite)...")
        # Forçamos o banco local se o principal falhar
        os.environ["DATABASE_URL"] = "sqlite:///trading_bot_fallback.db"
        init_db()

    
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

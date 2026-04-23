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

import http.server
import socketserver

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    
    class HealthCheckHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "Bot Trading Pro AI is running", "platform": "B3"}')
            
        def log_message(self, format, *args):
            # Suppress HTTP access logs so they don't spam the console
            pass

    with socketserver.TCPServer(("", port), HealthCheckHandler) as httpd:
        logger.info(f"Servidor HTTP (Web Service) ouvindo na porta {port}...")
        httpd.serve_forever()

if __name__ == "__main__":
    logger.info("🚀 Iniciando Sistema Trading Pro AI...")
    
    # Check for critical environment variables
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    discord_token = os.getenv("DISCORD_TOKEN")
    mp_token = os.getenv("MERCADO_PAGO_ACCESS_TOKEN")
    
    if not telegram_token and not discord_token:
        logger.error("❌ ERRO CRÍTICO: Nenhum token de bot (Telegram ou Discord) foi encontrado.")
        logger.error("Certifique-se de configurar as variáveis de ambiente no Render.")
    
    # Start Telegram Bot Thread
    if telegram_token:
        t_telegram = threading.Thread(target=run_telegram, name="TelegramThread", daemon=True)
        t_telegram.start()
        logger.info("✅ Thread do Telegram iniciada.")
    else:
        logger.warning("⚠️ Ignorando Telegram Bot (TOKEN ausente).")

    # Start Discord Bot Thread
    if discord_token:
        t_discord = threading.Thread(target=run_discord, name="DiscordThread", daemon=True)
        t_discord.start()
        logger.info("✅ Thread do Discord iniciada.")
    else:
        logger.warning("⚠️ Ignorando Discord Bot (TOKEN ausente).")

    # The HTTP Server runs on the main thread and is REQUIRED for Render Web Services
    try:
        run_http_server()
    except KeyboardInterrupt:
        logger.info("Stopping...")
    except Exception as e:
        logger.error(f"Erro no Servidor HTTP: {e}")


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

    # Inicia os bots em Threads separadas para não bloquear o servidor HTTP
    t_telegram = threading.Thread(target=run_telegram, daemon=True)
    t_discord = threading.Thread(target=run_discord, daemon=True)

    t_telegram.start()
    t_discord.start()

    # O servidor HTTP roda na thread principal, mantendo o processo do Render vivo
    try:
        run_http_server()
    except KeyboardInterrupt:
        logger.info("Servidor desligado.")

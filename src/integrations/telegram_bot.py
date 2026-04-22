import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from src.data.data_manager import DataManager
from src.models.predictor import TradingPredictor
from src.integrations.mercado_pago import PaymentManager
from src.database.db import get_user, create_or_update_user, init_db
from dotenv import load_dotenv

load_dotenv()

class TelegramBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.dm = DataManager()
        self.predictor = TradingPredictor()
        self.pm = PaymentManager()
        init_db()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        user = get_user(user_id)
        
        welcome_msg = (
            "🚀 *Bem-vindo ao Bot Trading Pro AI*\n\n"
            "Análise de mercado com alta precisão usando Machine Learning.\n\n"
            "🔹 /analisar - Receber sinal agora\n"
            "🔹 /vip - Tornar-se membro VIP (R$ 30,00)\n"
            "🔹 /ajuda - Ver comandos"
        )
        await update.message.reply_text(welcome_msg, parse_mode='Markdown')

    async def vip_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        payment_url = self.pm.create_payment_link(user_id, "telegram")
        
        keyboard = [[InlineKeyboardButton("Pagar R$ 30,00 (Pix/Cartão)", url=payment_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "💎 *Acesso VIP*\n\n"
            "Garanta acesso vitalício aos sinais de alta precisão.\n"
            "Após o pagamento, o sistema validará seu acesso automaticamente.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        user = get_user(user_id)
        
        # Check VIP status (Simple mock check for now - in production use check_payment_status)
        is_paid = self.pm.check_payment_status(f"telegram_{user_id}")
        if is_paid:
            create_or_update_user(user_id, "telegram", True)
            user = get_user(user_id)

        if not user or not user.is_vip:
            await update.message.reply_text(
                "❌ *Acesso Negado*\n\nEsta função é exclusiva para membros VIP.\nUse /vip para assinar.",
                parse_mode='Markdown'
            )
            return

        await update.message.reply_text("🔄 Analisando mercado... aguarde.")
        
        try:
            data = self.dm.fetch_data(period="5d", interval="5m")
            data_with_indicators = self.dm.add_indicators(data)
            
            # Load model and predict
            self.predictor.load_model()
            last_row = data_with_indicators.iloc[[-1]]
            prediction, prob = self.predictor.predict_next(last_row)
            
            signal = "🟢 COMPRA" if prediction == 1 else "🔴 VENDA"
            confidence = prob if prediction == 1 else (1 - prob)
            
            response = (
                f"📊 *ANÁLISE FINALIZADA*\n\n"
                f"Ativo: {self.dm.symbol}\n"
                f"Sinal: *{signal}*\n"
                f"Confiança: {confidence:.2%}\n"
                f"Estratégia: ML XGBoost V2\n\n"
                f"⚠️ *Gerenciamento:* Use Stop Loss técnico e nunca arrisque mais de 1% da banca."
            )
            await update.message.reply_text(response, parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"❌ Erro na análise: {str(e)}")

    def run(self):
        app = ApplicationBuilder().token(self.token).build()
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("vip", self.vip_command))
        app.add_handler(CommandHandler("analisar", self.analyze_command))
        print("Telegram Bot is running...")
        app.run_polling()

if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()

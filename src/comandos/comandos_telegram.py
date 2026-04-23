from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler
from src.database.db import get_user, create_or_update_user
from src.data.data_manager import DataManager
import logging
import datetime

logger = logging.getLogger("TelegramCommands")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name
    
    # Ensure user is registered to start the trial
    user = get_user(user_id)
    if not user:
        create_or_update_user(user_id, "telegram", False)
        user = get_user(user_id)

    welcome_msg = (
        f"👋 *Olá, {user_name}! Bem-vindo ao Bot Trading Pro AI*\n\n"
        "O sistema de inteligência artificial mais avançado para sinais na B3.\n\n"
        "🎁 *BÔNUS:* Você ganhou **7 DIAS GRÁTIS** de acesso total!\n"
        f"Seu período de teste começou em: {user.created_at.strftime('%d/%m/%Y')}\n\n"
        "📈 *O que eu faço?*\n"
        "Analiso volume e price action para prever a próxima tendência.\n\n"
        "📌 *Comandos:*\n"
        "• /analisar - Gera um sinal\n"
        "• /status - Ver quanto tempo de teste resta\n"
        "• /ajuda - Guia de uso"
    )
    
    keyboard = [
        [InlineKeyboardButton("📊 Analisar WDO", callback_data="analyze_WDO")],
        [InlineKeyboardButton("📈 Analisar WIN", callback_data="analyze_WIN")],
        [InlineKeyboardButton("💎 Tornar-se VIP", callback_data="get_vip")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_msg, parse_mode='Markdown', reply_markup=reply_markup)

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info_text = (
        "🤖 *Sobre a Inteligência Artificial*\n\n"
        "O Bot utiliza um modelo **XGBoost (Extreme Gradient Boosting)** treinado com dados históricos da B3.\n\n"
        "🔍 *Fatores de Decisão:*\n"
        "• **Volume:** Analisa a força do movimento.\n"
        "• **Price Action:** Detecta topos e fundos.\n"
        "• **Tendência:** Médias Móveis Exponenciais (9 e 21).\n"
        "• **Volatilidade:** Bandas de Bollinger."
    )
    await update.message.reply_text(info_text, parse_mode='Markdown')

async def suporte_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    suporte_text = (
        "🛠️ *Suporte Técnico*\n\n"
        "Fale diretamente com nosso suporte no Telegram:\n\n"
        "👉 @seu_suporte_aqui\n"
        "Horário: Segunda a Sexta, das 09:00 às 18:00."
    )
    await update.message.reply_text(suporte_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 *Guia de Uso do Bot Trading Pro*\n\n"
        "1️⃣ *Análise:* Use `/analisar WDO` ou `/analisar WIN`. Se não especificar, o padrão é WDO.\n"
        "2️⃣ *VIP:* O acesso VIP libera sinais ilimitados.\n"
        "3️⃣ *Gerenciamento:* NUNCA opere sem Stop Loss. O bot indica a tendência, mas o mercado é soberano.\n\n"
        "❓ *Dúvidas?* @seu_suporte"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user = get_user(user_id)
    if not user:
        create_or_update_user(user_id, "telegram", False)
        user = get_user(user_id)

    trial_days = 7
    days_used = (datetime.datetime.now() - user.created_at).days
    days_left = max(0, trial_days - days_used)
    
    status = "💎 VIP" if user.is_vip else "🆓 Teste Grátis"
    
    msg = (
        "👤 *Status da sua Conta*\n\n"
        f"ID: `{user_id}`\n"
        f"Plano: *{status}*\n"
    )
    
    if not user.is_vip:
        if days_left > 0:
            msg += f"⏳ Restam **{days_left} dias** de teste gratuito."
        else:
            msg += "❌ Seu teste gratuito **expirou**."
        msg += "\n\nUse /vip para liberar acesso vitalício."
        
    await update.message.reply_text(msg, parse_mode='Markdown')

async def analyze_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_instance, asset=None):
    query = update.callback_query
    if query:
        await query.answer()
        user_id = str(query.from_user.id)
        effective_update = query.message
    else:
        user_id = str(update.effective_user.id)
        effective_update = update.message
        if not asset and context.args:
            asset = context.args[0].upper()

    if not asset:
        asset = "WDO"

    user = get_user(user_id)
    if not user:
        create_or_update_user(user_id, "telegram", False)
        user = get_user(user_id)
    
    is_paid = bot_instance.pm.check_payment_status(f"telegram_{user_id}")
    if is_paid:
        create_or_update_user(user_id, "telegram", True)
        user = get_user(user_id)

    trial_days = 7
    trial_expired = (datetime.datetime.now() - user.created_at).days >= trial_days
    
    if not user.is_vip and trial_expired:
        msg = "❌ *Teste Expirado*\n\nSeus 7 dias grátis acabaram. Use /vip para assinar."
        if query:
            await query.edit_message_text(msg, parse_mode='Markdown')
        else:
            await effective_update.reply_text(msg, parse_mode='Markdown')
        return

    wait_msg = await effective_update.reply_text(f"🔄 *Analisando {asset}...*", parse_mode='Markdown')
    
    try:
        dm = DataManager(asset_type=asset)
        data = dm.fetch_data(period="5d", interval="5m")
        data_with_indicators = dm.add_indicators(data)
        
        bot_instance.predictor.load_model()
        last_row = data_with_indicators.iloc[[-1]]
        prediction, prob = bot_instance.predictor.predict_next(last_row)
        
        signal = "🟢 COMPRA" if prediction == 1 else "🔴 VENDA"
        confidence = prob if prediction == 1 else (1 - prob)
        strength = "🔥 FORTE" if confidence > 0.75 else "⚡ MODERADA"
        
        response = (
            f"📊 *ANÁLISE DE MERCADO B3*\n\n"
            f"Ativo: `{asset}`\n"
            f"Sinal: *{signal}*\n"
            f"Força: *{strength}*\n"
            f"Confiança: `{confidence:.2%}`\n\n"
            f"⚠️ Use stop loss técnico em todas as operações."
        )
        await wait_msg.edit_text(response, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Erro na análise Telegram: {e}")
        await wait_msg.edit_text(f"❌ *Erro:* Não foi possível obter dados para `{asset}` no momento. Tente novamente em instantes.")

async def vip_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_instance):
    user_id = str(update.effective_user.id)
    payment_url = bot_instance.pm.create_payment_link(user_id, "telegram")
    keyboard = [[InlineKeyboardButton("🚀 Pagar R$ 30,00", url=payment_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = "💎 *ACESSO VIP*\n\nClique no botão abaixo para assinar:"
    await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_instance):
    query = update.callback_query
    data = query.data
    if data.startswith("analyze_"):
        asset = data.split("_")[1]
        await analyze_handler(update, context, bot_instance, asset=asset)
    elif data == "get_vip":
        user_id = str(query.from_user.id)
        payment_url = bot_instance.pm.create_payment_link(user_id, "telegram")
        keyboard = [[InlineKeyboardButton("🚀 Pagar R$ 30,00", url=payment_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("💎 Para se tornar VIP:", reply_markup=reply_markup)

def setup_telegram_commands(app, bot_instance):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ajuda", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(CommandHandler("suporte", suporte_command))
    app.add_handler(CommandHandler("vip", lambda u, c: vip_handler(u, c, bot_instance)))
    app.add_handler(CommandHandler("analisar", lambda u, c: analyze_handler(u, c, bot_instance)))
    app.add_handler(CallbackQueryHandler(lambda u, c: button_callback(u, c, bot_instance)))

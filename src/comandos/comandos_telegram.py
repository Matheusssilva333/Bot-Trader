from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from src.database.db import get_user, create_or_update_user
from src.data.data_manager import DataManager
import logging
import datetime

logger = logging.getLogger("TelegramCommands")

# --- TEXTOS PREMIUM ---
BANNER_WELCOME = "🏛️ *TRADING PRO AI - SISTEMA QUANTITATIVO*"
MSG_WELCOME = (
    "Seja bem-vindo ao futuro da análise técnica.\n\n"
    "Nossa IA utiliza processamento de dados em tempo real e modelos de Machine Learning (XGBoost) "
    "para identificar exaustão de preço e tendências explosivas nos ativos da B3.\n\n"
    "🚀 *Você está no modo de teste gratuito (7 dias).* \n"
    "Aproveite a precisão da nossa análise sênior.\n\n"
    "👇 *Selecione uma ação abaixo:*"
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name
    
    user = get_user(user_id)
    if not user:
        create_or_update_user(user_id, "telegram", False)
        user = get_user(user_id)

    keyboard = [
        [InlineKeyboardButton("📊 Analisar WDO (Dólar)", callback_data="analyze_WDO")],
        [InlineKeyboardButton("📈 Analisar WIN (Índice)", callback_data="analyze_WIN")],
        [InlineKeyboardButton("💎 Assinar Acesso VIP", callback_data="get_vip")],
        [InlineKeyboardButton("👨‍💻 Suporte Técnico", callback_data="get_support")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"{BANNER_WELCOME}\n\n👋 Olá, {user_name}!\n{MSG_WELCOME}", 
        parse_mode='Markdown', 
        reply_markup=reply_markup
    )

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info_text = (
        "🧠 *TECNOLOGIA TRADING PRO AI*\n\n"
        "Nosso motor de decisão é baseado em **Aprendizado de Máquina Supervisionado**.\n\n"
        "🛡️ *O que analisamos:*\n"
        "• **Fluxo de Ordens:** Identificação de pressão compradora/vendedora.\n"
        "• **Price Action:** Padrões de reversão em tempo real.\n"
        "• **Estatística:** Desvios padrões via Bandas de Bollinger.\n"
        "• **IA Claude:** Parecer técnico qualitativo final."
    )
    await update.message.reply_text(info_text, parse_mode='Markdown')

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

    asset = asset or "WDO"
    
    # Typing indicator para parecer humano
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    wait_msg = await effective_update.reply_text(f"🔍 *Iniciando varredura técnica para {asset}...*", parse_mode='Markdown')
    
    try:
        dm = DataManager(asset_type=asset)
        data = dm.fetch_data(period="5d", interval="5m")
        data_with_indicators = dm.add_indicators(data)
        
        bot_instance.predictor.load_model()
        last_row = data_with_indicators.iloc[[-1]]
        prediction, prob = bot_instance.predictor.predict_next(last_row)
        
        signal = "🟢 COMPRA" if prediction == 1 else "🔴 VENDA"
        confidence = prob if prediction == 1 else (1 - prob)
        
        # Obter opinião da IA (Claude)
        indicators_dict = last_row.to_dict('records')[0]
        ai_opinion = await bot_instance.ai.get_market_opinion(asset, signal, confidence, indicators_dict)
        
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        response = (
            f"📡 *RELATÓRIO QUANTITATIVO - {asset}*\n"
            f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            f"🕒 Horário: `{timestamp}`\n"
            f"🎯 Sugestão: *{signal}*\n"
            f"⚡ Confiança: `{confidence:.2%}`\n"
            f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            f"📝 *PARECER DO ANALISTA AI:*\n"
            f"_{ai_opinion}_\n\n"
            f"⚠️ *Nota:* Esta é uma análise estatística. O mercado financeiro envolve riscos. Gerencie seu capital."
        )

        await wait_msg.edit_text(response, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Erro na análise: {e}")
        await wait_msg.edit_text(f"❌ *Ops!* Nossos servidores estão recebendo muitos dados de `{asset}` agora. Tente novamente em 1 minuto.")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user = get_user(user_id)
    
    status = "💎 VIP" if user and user.is_vip else "🆓 TESTE"
    msg = (
        "📈 *PAINEL DA CONTA*\n\n"
        f"• Status: *{status}*\n"
        "• Rede: `Telegram Quant Cluster`\n\n"
        "Sua licença permite acesso aos sinais de alta frequência da B3."
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_instance):
    """Responde ao chat usando a inteligência do Claude."""
    if not update.message or not update.message.text: return
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    response = await bot_instance.ai.chat_with_user(update.message.text)
    await update.message.reply_text(response)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_instance):
    query = update.callback_query
    data = query.data
    if data.startswith("analyze_"):
        asset = data.split("_")[1]
        await analyze_handler(update, context, bot_instance, asset=asset)
    elif data == "get_vip":
        user_id = str(query.from_user.id)
        payment_url = bot_instance.pm.create_payment_link(user_id, "telegram")
        keyboard = [[InlineKeyboardButton("💳 Assinar VIP (R$ 30,00)", url=payment_url)]]
        await query.message.reply_text("💎 *OPERAÇÕES ILIMITADAS*\nAssine para liberar todos os recursos:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    elif data == "get_support":
        await query.message.reply_text("🛠️ *SUPORTE TRADING PRO*\nFale com @seu_suporte_aqui\nAtendimento: 09h às 18h.", parse_mode='Markdown')

def setup_telegram_commands(app, bot_instance):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analisar", lambda u, c: analyze_handler(u, c, bot_instance)))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(CommandHandler("vip", lambda u, c: button_callback(u, c, bot_instance))) # Reutiliza lógica
    app.add_handler(CallbackQueryHandler(lambda u, c: button_callback(u, c, bot_instance)))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: chat_handler(u, c, bot_instance)))

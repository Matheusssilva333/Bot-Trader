from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler
from src.database.db import get_user, create_or_update_user
from src.data.data_manager import DataManager
import logging

logger = logging.getLogger("TelegramCommands")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name
    
    welcome_msg = (
        f"👋 *Olá, {user_name}! Bem-vindo ao Bot Trading Pro AI*\n\n"
        "O sistema de inteligência artificial mais avançado para sinais na B3 (Mini Índice e Mini Dólar).\n\n"
        "📈 *O que eu faço?*\n"
        "Analiso volume, price action e indicadores técnicos usando XGBoost para prever a próxima tendência.\n\n"
        "📌 *Comandos principais:*\n"
        "• /analisar - Gera um sinal em tempo real\n"
        "• /vip - Adquira acesso vitalício\n"
        "• /ajuda - Tutorial completo"
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
        "• **Price Action:** Detecta topos e fundos (Donchian Channels).\n"
        "• **Tendência:** Médias Móveis Exponenciais (9 e 21 períodos).\n"
        "• **Volatilidade:** Bandas de Bollinger.\n\n"
        "O modelo busca padrões que precedem movimentos de alta ou baixa com probabilidade estatística calculada em tempo real."
    )
    await update.message.reply_text(info_text, parse_mode='Markdown')

async def suporte_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    suporte_text = (
        "🛠️ *Suporte Técnico*\n\n"
        "Está com problemas ou tem dúvidas sobre o bot?\n"
        "Fale diretamente com nosso suporte no Telegram:\n\n"
        "👉 @seu_suporte_aqui\n\n"
        "Horário de atendimento: Segunda a Sexta, das 09:00 às 18:00."
    )
    await update.message.reply_text(suporte_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 *Guia de Uso do Bot Trading Pro*\n\n"
        "1️⃣ *Análise:* Use `/analisar WDO` ou `/analisar WIN`. Se não especificar, o padrão é WDO.\n"
        "2️⃣ *VIP:* O acesso VIP libera sinais ilimitados. Sem o VIP, você tem acesso limitado ou apenas demonstrações.\n"
        "3️⃣ *Gerenciamento:* NUNCA opere sem Stop Loss. O bot indica a tendência, mas o mercado é soberano.\n\n"
        "❓ *Dúvidas?* Entre em contato com o suporte @seu_suporte"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user = get_user(user_id)
    
    status = "💎 VIP" if user and user.is_vip else "🆓 Gratuito"
    
    msg = (
        "👤 *Status da sua Conta*\n\n"
        f"ID: `{user_id}`\n"
        f"Plano: *{status}*\n"
    )
    
    if not user or not user.is_vip:
        msg += "\n⚠️ Você está no plano limitado. Use /vip para liberar todas as funções."
        
    await update.message.reply_text(msg, parse_mode='Markdown')

async def analyze_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_instance, asset=None):
    # This can be called from command or callback
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
    
    # Check VIP status (Sync with Mercado Pago)
    is_paid = bot_instance.pm.check_payment_status(f"telegram_{user_id}")
    if is_paid:
        create_or_update_user(user_id, "telegram", True)
        user = get_user(user_id)

    if not user or not user.is_vip:
        msg = "❌ *Acesso Negado*\n\nEsta função é exclusiva para membros VIP.\nUse /vip para assinar."
        if query:
            await query.edit_message_text(msg, parse_mode='Markdown')
        else:
            await effective_update.reply_text(msg, parse_mode='Markdown')
        return

    wait_msg = await effective_update.reply_text(f"🔄 *Analisando {asset}...* extraindo indicadores de volume e preço.", parse_mode='Markdown')
    
    try:
        dm = DataManager(asset_type=asset)
        data = dm.fetch_data(period="5d", interval="5m")
        data_with_indicators = dm.add_indicators(data)
        
        bot_instance.predictor.load_model()
        last_row = data_with_indicators.iloc[[-1]]
        prediction, prob = bot_instance.predictor.predict_next(last_row)
        
        signal = "🟢 COMPRA" if prediction == 1 else "🔴 VENDA"
        confidence = prob if prediction == 1 else (1 - prob)
        
        # Determine color/emoji based on confidence
        strength = "🔥 FORTE" if confidence > 0.75 else "⚡ MODERADA"
        
        response = (
            f"📊 *ANÁLISE DE MERCADO B3*\n\n"
            f"Ativo: `{asset}`\n"
            f"Sinal: *{signal}*\n"
            f"Força: *{strength}*\n"
            f"Confiança: `{confidence:.2%}`\n\n"
            f"🎯 *Pontos de Atenção:*\n"
            f"• Suporte/Resistência detectados\n"
            f"• Tendência confirmada por Volume\n"
            f"• Estratégia: XGBoost Pro V2\n\n"
            f"⚠️ *Aviso:* Use stop loss. Lucros passados não garantem lucros futuros."
        )
        
        await wait_msg.edit_text(response, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Erro na análise: {e}")
        await wait_msg.edit_text(f"❌ *Erro:* Ocorreu um problema ao buscar dados do ativo {asset}.")

async def vip_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_instance):
    user_id = str(update.effective_user.id)
    payment_url = bot_instance.pm.create_payment_link(user_id, "telegram")
    
    keyboard = [[InlineKeyboardButton("🚀 Pagar via Pix (R$ 30,00)", url=payment_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    msg = (
        "💎 *VANTAGENS DO ACESSO VIP*\n\n"
        "✅ Sinais ilimitados para WIN e WDO\n"
        "✅ Maior precisão (Modelos 2.0)\n"
        "✅ Suporte prioritário\n"
        "✅ Acesso vitalício (Sem mensalidade)\n\n"
        "Clique no botão abaixo para gerar seu QR Code ou Link Pix:"
    )
    
    await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_instance):
    query = update.callback_query
    data = query.data
    
    if data.startswith("analyze_"):
        asset = data.split("_")[1]
        await analyze_handler(update, context, bot_instance, asset=asset)
    elif data == "get_vip":
        # Simulating a call to vip_handler logic but for callback
        user_id = str(query.from_user.id)
        payment_url = bot_instance.pm.create_payment_link(user_id, "telegram")
        keyboard = [[InlineKeyboardButton("🚀 Pagar via Pix (R$ 30,00)", url=payment_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("💎 Para se tornar VIP, clique no botão abaixo:", reply_markup=reply_markup)

def setup_telegram_commands(app, bot_instance):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ajuda", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(CommandHandler("suporte", suporte_command))
    app.add_handler(CommandHandler("vip", lambda u, c: vip_handler(u, c, bot_instance)))
    app.add_handler(CommandHandler("analisar", lambda u, c: analyze_handler(u, c, bot_instance)))
    
    # Callback queries for buttons
    app.add_handler(CallbackQueryHandler(lambda u, c: button_callback(u, c, bot_instance)))

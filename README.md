# Bot Trading Pro AI 🚀

Sistema profissional de análise de Day Trading com Machine Learning e API do Claude integrado ao Telegram.

## 🛠️ Funcionalidades
- **Predição por IA**: Utiliza algoritmos XGBoost treinados com indicadores técnicos (RSI, MACD, Médias Móveis, etc).
- **Monetização Integrada**: Sistema de assinatura automática via Mercado Pago (R$ 30,00).
- **Multi-Plataforma**: Comandos disponíveis no Telegram e Discord.
- **Base de Dados**: Persistência de usuários e status VIP em SQLite.

## 🚀 Como Configurar

### 1. Requisitos
- Python 3.10 ou superior.
- Instalar dependências: `pip install -r requirements.txt`

### 2. Configuração de APIs
Renomeie o arquivo `.env.example` para `.env` e preencha suas chaves:
- `TELEGRAM_TOKEN`: Pegue com o [@BotFather](https://t.me/botfather).
- `DISCORD_TOKEN`: No [Portal de Desenvolvedores do Discord](https://discord.com/developers/applications).
- `MERCADO_PAGO_ACCESS_TOKEN`: No painel do [Mercado Pago Developers](https://www.mercadopago.com.br/developers/pt/panel).

### 3. Treinamento Inicial
Antes de rodar o bot, você precisa treinar a inteligência artificial com dados históricos:
```bash
python train_model.py
```

### 4. Execução
Para iniciar os dois bots simultaneamente:
```bash
python main.py
```

## 📊 Comandos
- `/start` (Telegram) | `!start` (Discord) - Inicia o bot.
- `/vip` (Telegram) | `!vip` (Discord) - Gera link de pagamento de R$ 30,00.
- `/analisar` (Telegram) | `!analisar` (Discord) - Realiza predição do ativo (Apenas VIP).

## ⚠️ Aviso Legal
Este software é uma ferramenta de auxílio baseada em estatística e probabilidade. O mercado financeiro possui riscos inerentes. 100% de precisão é um objetivo matemático buscado pelo modelo, mas não uma garantia de lucro. Use sempre com gerenciamento de risco.

# Bot Trading Pro AI 🚀

Sistema profissional de análise de Day Trading com Machine Learning e API do Claude integrado ao Telegram.

## 🛠️ Funcionalidades
- **Predição por IA**: Utiliza algoritmos XGBoost treinados com indicadores técnicos (RSI, MACD, Médias Móveis, etc).
- **Monetização Integrada**: Sistema de assinatura automática via Mercado Pago (R$ 30,00).
- **Base de Dados**: Persistência de usuários e status VIP em SQLite.

## 🚀 Como Configurar

### 1. Requisitos
- Python 3.10 ou superior.
- Instalar dependências: `pip install -r requirements.txt`

### 2. Configuração de APIs
Renomeie o arquivo `.env.example` para `.env` e preencha suas chaves:
- `TELEGRAM_TOKEN`: Pegue com o [@BotFather](https://t.me/botfather).
- `MERCADO_PAGO_ACCESS_TOKEN`: No painel do [Mercado Pago Developers](https://www.mercadopago.com.br/developers/pt/panel).

### 3. Treinamento Inicial
Antes de rodar o bot, você precisa treinar a inteligência artificial com dados históricos:
```bash
python train_model.py
```

### 4. Execução
Para iniciar o bot:
```bash
python main.py
```

## 📊 Comandos
- `/start` (Telegram) | - Inicia o bot.
- `/vip` (Telegram) | - Gera link de pagamento de R$ 30,00.
- `/analisar` (Telegram) | - Realiza predição do ativo (Apenas VIP).

## ⚠️ Aviso Legal
Este software é uma ferramenta de auxílio baseada em estatística e probabilidade. O mercado financeiro possui riscos inerentes. 100% de precisão é um objetivo matemático buscado pelo modelo, mas não uma garantia de lucro. Use sempre com gerenciamento de risco.

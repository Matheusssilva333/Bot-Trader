import anthropic
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("ClaudeAI")

class ClaudeAnalyzer:
    """
    Integrates Claude AI to provide technical reasoning for trade signals.
    """
    
    def __init__(self):
        api_key = os.getenv("CLAUDE_API_KEY")
        if not api_key or api_key == "seu_token_claude_aqui":
            logger.warning("CLAUDE_API_KEY não configurada corretamente.")
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=api_key)

    async def get_market_opinion(self, asset: str, signal: str, confidence: float, indicators: dict):
        """
        Sends technical data to Claude and returns a human-readable analysis.
        """
        if not self.client:
            return "Análise detalhada via IA indisponível (Chave não configurada)."

        try:
            prompt = (
                f"Você é um analista sênior de trading na B3. Acabamos de gerar um sinal para {asset}.\n\n"
                f"📊 **Dados Técnicos:**\n"
                f"- Sinal sugerido: {signal}\n"
                f"- Confiança do modelo XGBoost: {confidence:.2%}\n"
                f"- Preço Atual: {indicators.get('close')}\n"
                f"- RSI (2 períodos): {indicators.get('rsi', 'N/A')}\n"
                f"- Distância da Banda Superior: {indicators.get('bb_high', 'N/A')}\n"
                f"- Distância da Banda Inferior: {indicators.get('bb_low', 'N/A')}\n\n"
                "Forneça uma explicação técnica curta (máximo 3 frases) em português do Brasil "
                "justificando este sinal com base no Price Action e nos indicadores. Seja profissional e direto."
            )

            message = self.client.messages.create(
                model="claude-3-haiku-20240307", # Fast and cost-effective for signals
                max_tokens=150,
                temperature=0.5,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Erro ao consultar Claude: {e}")
            return "Erro ao processar análise avançada via Claude."

    async def chat_with_user(self, user_message: str):
        """
        Handles general conversation with the user using Claude AI.
        """
        if not self.client:
            return "Chat indisponível (Chave API não configurada)."

        try:
            prompt = (
                "Você é o 'Bot Trading Pro AI', um assistente especializado em mercado financeiro (B3). "
                "Sua personalidade é prestativa, profissional e focada em resultados. "
                "Ajude o usuário com dúvidas sobre trading, o bot, ou o mercado em geral. "
                "Mantenha respostas concisas e objetivas.\n\n"
                f"Usuário diz: {user_message}"
            )

            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=300,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Erro no chat Claude: {e}")
            return "Desculpe, tive um problema ao processar sua mensagem."


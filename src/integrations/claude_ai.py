import anthropic
import os
import logging

logger = logging.getLogger("ClaudeAI")


def _anthropic_error_blob(exc: BaseException) -> str:
    """Junta mensagem da exceção + corpo JSON (Anthropic devolve detalhes em body)."""
    chunks = [str(exc), repr(exc)]
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        chunks.append(str(body))
        err = body.get("error")
        if isinstance(err, dict):
            chunks.append(str(err.get("message", "")))
    return " ".join(chunks).lower()


def _is_quota_or_billing_error(exc: BaseException) -> bool:
    blob = _anthropic_error_blob(exc)
    return any(
        s in blob
        for s in (
            "credit balance is too low",
            "insufficient_quota",
            "billing",
            "rate_limit",
            "overloaded",
        )
    )


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
            self.client = anthropic.AsyncAnthropic(api_key=api_key)

    async def get_market_opinion(self, asset: str, signal: str, confidence: float, indicators: dict):
        """
        Sends technical data to Claude and returns a human-readable analysis.
        """
        if not self.client:
            return "Análise detalhada via IA indisponível (Chave não configurada)."

        try:
            prompt = (
                f"Aja como um analista quantitativo sênior de mesa proprietária. Sinal para {asset}.\n\n"
                f"📊 **Métricas Técnicas:**\n"
                f"- Direção Sugerida: {signal}\n"
                f"- Confiança do Algoritmo XGBoost: {confidence:.2%}\n"
                f"- Preço de Fechamento: {indicators.get('close')}\n"
                f"- Médias Móveis: EMA9 @ {indicators.get('ema_9')}, EMA21 @ {indicators.get('ema_21')}\n"
                f"- Volatilidade: Bandas de Bollinger {indicators.get('bb_high')} / {indicators.get('bb_low')}\n"
                f"- Momentum: RSI14 @ {indicators.get('rsi_14', 'N/A')}\n\n"
                "Instrução: Forneça um parecer técnico extremamente conciso (máximo 250 caracteres) "
                "em português. Foque no motivo principal (ex: exaustão, rompimento, tendência). "
                "Seja direto e autoritativo."
            )

            message = await self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=150,
                temperature=0.5,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Erro ao consultar Claude: {e}")
            if _is_quota_or_billing_error(e):
                return (
                    "💡 *Nota do Analista:* O sinal atual baseia-se em forte confluência técnica de indicadores. "
                    "A tendência mostra força e o volume confirma a direção sugerida."
                )
            return "Análise técnica baseada em indicadores quantitativos."

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

            message = await self.client.messages.create(
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
            if _is_quota_or_billing_error(e):
                return (
                    "Estou temporariamente sem acesso à IA de conversação (créditos ou limite). "
                    "Use /analisar para o sinal quantitativo ou /suporte."
                )
            return "Desculpe, tive um erro ao processar sua pergunta. Pode tentar novamente?"

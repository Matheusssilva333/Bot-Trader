import mercadopago
import os
from dotenv import load_dotenv

load_dotenv()

class PaymentManager:
    """
    Manages subscription payments using Mercado Pago.
    """
    
    def __init__(self):
        access_token = os.getenv("MERCADO_PAGO_ACCESS_TOKEN")
        if not access_token:
            print("Warning: MERCADO_PAGO_ACCESS_TOKEN not found in .env")
        self.sdk = mercadopago.SDK(access_token)

    def create_payment_link(self, user_id: str, platform: str):
        """
        Creates a payment preference for the R$ 30,00 subscription.
        """
        payment_data = {
            "items": [
                {
                    "id": f"sub_{user_id}",
                    "title": "Acesso VIP - Bot Trading Pro",
                    "quantity": 1,
                    "currency_id": "BRL",
                    "unit_price": 30.00
                }
            ],
            "external_reference": f"{platform}_{user_id}",
            "back_urls": {
                "success": "https://t.me/your_bot_user", # Optional
                "pending": "https://t.me/your_bot_user",
                "failure": "https://t.me/your_bot_user"
            },
            "auto_return": "approved"
        }

        result = self.sdk.preference().create(payment_data)
        if result["status"] == 201:
            return result["response"]["init_point"] # Return the checkout URL
        else:
            print(f"Error creating payment: {result}")
            return None

    def check_payment_status(self, external_reference: str):
        """
        Checks if a user has a confirmed payment.
        """
        # In a real production environment, you should use Webhooks.
        # This is a simplified search for manual check or polling.
        filters = {
            "external_reference": external_reference,
            "status": "approved"
        }
        
        search_result = self.sdk.payment().search(filters)
        if search_result["status"] == 200:
            payments = search_result["response"]["results"]
            return len(payments) > 0
        return False

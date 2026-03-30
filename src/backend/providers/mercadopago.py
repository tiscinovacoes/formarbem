import mercadopago
from .base import PaymentProvider

class MercadoPagoProvider(PaymentProvider):
    def __init__(self, access_token, base_url):
        self.sdk = mercadopago.SDK(access_token)
        self.base_url = base_url.rstrip("/")

    def create_checkout_url(self, item_id, title, price, quantity=1):
        preference_data = {
            "items": [
                {
                    "id": item_id,
                    "title": title,
                    "quantity": quantity,
                    "unit_price": float(price),
                    "currency_id": "BRL"
                }
            ],
            "back_urls": {
                "success": f"{self.base_url}/sucesso",
                "failure": f"{self.base_url}/erro",
                "pending": f"{self.base_url}/pendente"
            },
            "auto_return": "approved",
            "notification_url": f"{self.base_url}/api/webhooks/mercadopago", # Ajustado para o prefixo /api se necessário
            "external_reference": item_id
        }
        
        preference_response = self.sdk.preference().create(preference_data)
        preference = preference_response["response"]
        return preference["init_point"]

    def get_payment_status(self, payment_id):
        payment_info = self.sdk.payment().get(payment_id)
        return payment_info["response"]["status"]

    def handle_webhook(self, data):
        # Implementation to verify and update course access
        if data.get("action") == "payment.created":
            payment_id = data.get("data", {}).get("id")
            return self.get_payment_status(payment_id)
        return None

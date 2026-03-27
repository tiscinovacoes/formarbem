from abc import ABC, abstractmethod

class PaymentProvider(ABC):
    @abstractmethod
    def create_checkout_url(self, item_id, title, price, quantity=1):
        """Returns the URL for the user to complete the payment."""
        pass

    @abstractmethod
    def get_payment_status(self, payment_id):
        """Checks the status of a specific payment."""
        pass

    @abstractmethod
    def handle_webhook(self, data):
        """Processes incoming data from the payment gateway webhook."""
        pass

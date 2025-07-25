from core.clients.client import Client
from core.order.order import Order

class GeminiClient(Client):
    def __init__(self, state_obj):
        self.state = state_obj

    def place_order(self, order: Order):
        print(f"[Gemini] Placing {order}")

    def check_orders_for_execution(self):
        print(f"[Gemini] Checking orders for execution...")
    def fulfill_order(self, order: Order):
        print(f"[Gemini] Fulfilling {order}")

    def cancel_order(self, order: Order):
        print(f"[Gemini] Cancelling {order}")
from abc import ABC, abstractmethod

from core.order.order import Order

class Client(ABC):

    @abstractmethod
    def place_order(self, order: Order):
        """Place a new order."""
        pass

    @abstractmethod
    def check_orders_for_execution(self):
        """Check if any orders are ready for execution."""
        pass

    @abstractmethod
    def fulfill_order(self, order: Order):
        """Fulfill an existing order."""
        pass

    @abstractmethod
    def cancel_order(self, order: Order):
        """Cancel an existing order."""
        pass

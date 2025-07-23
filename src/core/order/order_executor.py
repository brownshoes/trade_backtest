from abc import ABC, abstractmethod

class OrderExecutor(ABC):
    @abstractmethod
    def execute(self, order, state_obj):
        pass

    @abstractmethod
    def complete(self, order, state_obj):
        pass

class BackTestExecutor(OrderExecutor):
    def execute(self, order, state_obj):
        print("Executing order on Gemini")
        # Implementation here

    def complete(self, order, state_obj):
        print("Completing order on Gemini")
        # Implementation here


class GeminiExecutor(OrderExecutor):
    def execute(self, order, state_obj):
        print("Executing order on Gemini")
        # Implementation here

    def complete(self, order, state_obj):
        print("Completing order on Gemini")
        # Implementation here

def executor_factory(order_executor_name: str) -> OrderExecutor:
    executors = {
        "GEMINI": GeminiExecutor,
        "BACKTEST": BackTestExecutor,
        # add more as needed
    }
    executor_class = executors.get(order_executor_name.upper())
    if not executor_class:
        raise ValueError(f"No executor found for exchange: {order_executor_name}")
    return executor_class()
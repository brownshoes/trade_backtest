from core.clients.backtest_client import BacktestClient
from core.clients.gemini_client import GeminiClient
from core.clients.client import Client

def client_factory(client_name: str, state_obj, order_completion, client_api=None) -> Client:
    clients = {
        "GEMINI": GeminiClient,
        "BACKTEST": BacktestClient,
        # add more as needed
    }
    client_class = clients.get(client_name.upper())
    if not client_class:
        raise ValueError(f"No client found for exchange: {client_name}")

    return client_class(
        state_obj=state_obj,
        order_completion=order_completion,
        client_api=client_api,
    )
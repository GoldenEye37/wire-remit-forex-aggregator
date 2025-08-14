from .base_provider import BaseProviderClient
from .exchange_rate_client import ExchangeRateClient
from .fixer_io_client import FixerIOClient
from .polygon_client import PolygonClient

PROVIDER_CLIENTS = {
    "fixer": FixerIOClient,
    "exchange_rate": ExchangeRateClient,
    "polygon": PolygonClient,
}

def get_provider_client(provider_name: str) -> BaseProviderClient:
    """
    Factory to instantiate provider client by name.
    """
    client_class = PROVIDER_CLIENTS.get(provider_name)
    if not client_class:
        raise ValueError(f"Unknown provider: {provider_name}")
    return client_class()

from app.services.providers.base_provider import BaseProviderClient
from app.services.providers.currency_layer_client import CurrencyLayerClient
from app.services.providers.exchange_rate_client import ExchangeRateClient
from app.services.providers.fixer_io_client import FixerIOClient
from app.services.providers.polygon_client import PolygonClient

PROVIDER_CLIENTS = {
    "fixer": FixerIOClient,
    "exchange_rate": ExchangeRateClient,
    "polygon": PolygonClient,
    "currency_layer": CurrencyLayerClient,
}

def get_provider_client(provider_name: str) -> BaseProviderClient:
    """
    Factory to instantiate provider client by name.
    """
    client_class = PROVIDER_CLIENTS.get(provider_name)
    if not client_class:
        raise ValueError(f"Unknown provider: {provider_name}")
    return client_class()

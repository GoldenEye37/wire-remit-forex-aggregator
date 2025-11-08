from app.services.providers.base_provider import BaseProviderClient


def _get_provider_class(provider_name: str):
    """
    Lazy import provider classes to avoid import errors for unused providers.
    """
    if provider_name == "fixer":
        from app.services.providers.fixer_io_client import FixerIOClient

        return FixerIOClient
    elif provider_name == "exchange_rate":
        from app.services.providers.exchange_rate_client import ExchangeRateClient

        return ExchangeRateClient
    elif provider_name == "polygon":
        from app.services.providers.polygon_client import PolygonClient

        return PolygonClient
    elif provider_name == "currency_layer":
        from app.services.providers.currency_layer_client import CurrencyLayerClient

        return CurrencyLayerClient
    else:
        return None


# Keep for backwards compatibility and discovery
PROVIDER_CLIENTS = {
    "fixer": "FixerIOClient",
    "exchange_rate": "ExchangeRateClient",
    "polygon": "PolygonClient",
    "currency_layer": "CurrencyLayerClient",
}


def get_provider_client(provider_name: str) -> BaseProviderClient:
    """
    Factory to instantiate provider client by name.
    Uses lazy imports to avoid loading unused providers.
    """
    client_class = _get_provider_class(provider_name)
    if not client_class:
        raise ValueError(f"Unknown provider: {provider_name}")
    return client_class()

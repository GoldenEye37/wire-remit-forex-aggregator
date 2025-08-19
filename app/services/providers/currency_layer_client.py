import os
from datetime import datetime

import requests
from loguru import logger

from .base_provider import BaseProviderClient


class CurrencyLayerClient(BaseProviderClient):
    """
    Currency Layer API client for fetching forex rates.
    API Documentation: https://currencylayer.com/documentation
    """

    BASE_URL = "http://apilayer.net/api"

    def __init__(self):
        self.api_key = os.getenv("CURRENCY_LAYER_API_KEY")
        self.timeout = 10

        if not self.api_key:
            raise ValueError("CURRENCY_LAYER_API_KEY environment variable is required")

    def get_rates(
        self, source_currency: str = "USD", target_currencies: list[str] = None
    ) -> dict:
        """
        Fetch live exchange rates from Currency Layer API.

        Args:
            source_currency: Base currency (default: USD)
            target_currencies: List of target currencies to fetch rates for

        Returns:
            Dict containing rate data
        """
        try:
            params = {
                "access_key": self.api_key,
                "source": source_currency.upper(),
                "format": 1,  # JSON format
            }

            if target_currencies:
                currencies_str = ",".join([curr.upper() for curr in target_currencies])
                params["currencies"] = currencies_str

            url = f"{self.BASE_URL}/live"
            logger.info(
                f"Fetching rates from Currency Layer: {source_currency} -> {target_currencies}"
            )

            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            if not data.get("success", False):
                error_info = data.get("error", {})
                error_code = error_info.get("code")
                error_message = error_info.get("info", "Unknown error")
                raise Exception(
                    f"Currency Layer API error {error_code}: {error_message}"
                )

            logger.info(
                f"Successfully fetched {len(data.get('quotes', {}))} rates from Currency Layer"
            )

            """
            expected response from api client:

            {
                "success":true,
                "terms":"https:\/\/currencylayer.com\/terms",
                "privacy":"https:\/\/currencylayer.com\/privacy",
                "timestamp":1755522081,
                "source":"ZAR",
                "quotes":{
                    "ZAREUR":0.048646,
                    "ZARGBP":0.041934,
                    "ZARCAD":0.078339,
                    "ZARPLN":0.206886
                }
            }
            """
            # Convert Currency Layer response to standardized format
            conversion_rates = {}
            quotes = data.get("quotes", {})
            source = data.get("source", source_currency.upper())

            # Extract rates from quotes (format: USDEUR -> EUR: rate)
            for quote_key, rate_value in quotes.items():
                if quote_key.startswith(source):
                    target_currency = quote_key[len(source) :]  # Remove source prefix
                    conversion_rates[target_currency] = float(rate_value)

            # Convert timestamp to UTC string format
            timestamp = data.get("timestamp")
            if timestamp:
                # Convert Unix timestamp to UTC string
                dt = datetime.fromtimestamp(timestamp)
                last_update_utc = dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
            else:
                last_update_utc = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")

            response = {
                "base_code": source,
                "conversion_rates": conversion_rates,
                "last_update_utc": last_update_utc,
                "next_update_utc": None,  # Currency Layer doesn't provide this
            }
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Currency Layer API request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Currency Layer client error: {e}")
            raise

    def health_check(self):
        return super().health_check()
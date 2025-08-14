# Exchange Rate API Client 
import requests
import app

from loguru import logger  # Fixed typo

class ExchangeRateClient:
    BASE_URL = "https://v6.exchangerate-api.com/v6"

    def __init__(self):
        self.api_key = app.config["EXCHANGE_RATE_API_KEY"]

    def get_latest_rates(self, base_currency: str) -> dict:
        """
        Fetch latest exchange rates for the given base currency.
        Returns the parsed JSON response or raises an exception on error.
        """
        url = f"{self.BASE_URL}/{self.api_key}/latest/{base_currency}"
        logger.info(f"Requesting ExchangeRate API: {url}")
        try:
            response = requests.get(url, timeout=10)
            logger.debug(f"ExchangeRate API raw response: {response.text}")
            response.raise_for_status()
            data = response.json()
            if data.get("result") != "success":
                logger.error(f"ExchangeRate API error: {data}")
                raise ValueError(f"API error: {data}")

            logger.info(f"ExchangeRate API success for base_currency={base_currency}")
            response = {
                "base_code": data["base_code"],
                "conversion_rates": data["conversion_rates"],
                "last_update_utc": data["time_last_update_utc"],
                "next_update_utc": data["time_next_update_utc"],
            }
            logger.debug(f"ExchangeRate API processed response:\n {response}")
            return response
        except Exception as e:
            logger.exception(f"Error fetching rates from ExchangeRate API: {e}")
            raise e 
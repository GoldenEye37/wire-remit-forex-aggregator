# Fixer.io client
import requests
import app

from loguru import logger

class FixerIOClient:
    BASE_URL = "http://data.fixer.io/api/latest"

    def __init__(self):
        self.api_key = app.config["FIXER_API_KEY"]

    def get_latest_rates(self) -> dict:
        """
        Fetch latest exchange rates from Fixer.io.
        The base currency is always EUR.
        Returns the parsed JSON response or raises an exception on error.
        """
        params = {"access_key": self.api_key}
        logger.info(f"Requesting Fixer.io rates with params: {params}")
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            logger.debug(f"Fixer.io raw response: {response.text}")
            response.raise_for_status()
            data = response.json()
            if not data.get("success"):
                logger.error(f"Fixer.io API error: {data}")
                raise ValueError(f"API error: {data}")
            logger.info("Fixer.io API request successful")
            return {
                "base": data["base"],
                "date": data["date"],
                "rates": data["rates"],
                "timestamp": data["timestamp"],
            }
        except Exception as e:
            logger.exception(f"Error fetching rates from Fixer.io: {e}")
            raise e
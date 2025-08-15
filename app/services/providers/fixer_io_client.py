# Fixer.io client
import requests
from flask import current_app as app
from loguru import logger

from .base_provider import BaseProviderClient


class FixerIOClient(BaseProviderClient):
    BASE_URL = "http://data.fixer.io/api/latest"

    def __init__(self):
        self.api_key = app.config["FIXER_API_KEY"]

    def get_rates(self) -> dict:
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
                "base_code": data["base"],
                "date": data["date"],
                "conversion_rates": data["rates"],
                "last_update_utc": data["timestamp"],
            }
        except Exception as e:
            logger.exception(f"Error fetching rates from Fixer.io: {e}")
            raise e

    def health_check(self) -> dict:
        """
        Health check for Fixer.io API.
        Returns dict with status and details.
        """
        params = {"access_key": self.api_key}
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            if data.get("success"):
                return {"status": True, "details": "Fixer.io API reachable and returned success."}
            return {"status": False, "details": f"Fixer.io API error: {data}"}
        except Exception as e:
            logger.error(f"Fixer.io health check failed: {e}")
            return {"status": False, "details": str(e)}
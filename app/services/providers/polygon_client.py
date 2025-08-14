# Polygon API client
from loguru import logger
from polygon import RESTClient

import app

from .base_provider import BaseProviderClient


class PolygonClient(BaseProviderClient):
    def __init__(self):
        self.client = RESTClient(app.config["POLYGON_API_KEY"])

    def get_rates(
        self,
        from_currency: str,
        to_currency: str,
        amount: float = 1.0,
        precision: int = 2,
    ) -> dict:
        """
        Fetch real-time currency conversion from Polygon.
        Returns a standardized response dict.
        """
        logger.info(
            f"Requesting Polygon conversion: {amount} {from_currency} -> {to_currency} (precision={precision})"
        )
        try:
            response = self.client.get_real_time_currency_conversion(
                from_currency,
                to_currency,
                amount=amount,
                precision=precision,
            )
            logger.debug(f"Polygon API raw response: {response}")
            result = {
                "base_code": response.get("from"),
                "target_code": response.get("to"),
                "conversion_rate": response.get("last", {}).get("ask"),
                "conversion_bid": response.get("last", {}).get("bid"),
                "converted_amount": response.get("converted"),
                "initial_amount": response.get("initialAmount"),
                "last_update_utc": response.get("last", {}).get("timestamp"),
                "symbol": response.get("symbol"),
                "status": response.get("status"),
                "provider": "polygon",
            }
            logger.info("Polygon API request successful")
            return result
        except Exception as e:
            logger.exception(f"Error fetching conversion from Polygon: {e}")
            raise e

    def health_check(self) -> dict:
        """
        Health check for Polygon API.
        Returns dict with status and details.
        """
        try:
            # Use a common currency pair for health check
            response = self.client.get_real_time_currency_conversion("USD", "EUR", amount=1, precision=2)
            if response.get("status") == "success":
                return {"status": True, "details": "Polygon API reachable and returned success."}
            return {"status": False, "details": f"Polygon API error: {response}"}
        except Exception as e:
            logger.error(f"Polygon API health check failed: {e}")
            return {"status": False, "details": str(e)}

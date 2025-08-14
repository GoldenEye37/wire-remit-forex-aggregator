# Polygon API client
import app

from polygon import RESTClient
from loguru import logger


class PolygonClient:
    def __init__(self):
        self.client = RESTClient(app.config["POLYGON_API_KEY"])

    def get_real_time_currency_conversion(self, from_currency: str, to_currency: str, amount: float = 1.0, precision: int = 2) -> dict:
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
                "timestamp": response.get("last", {}).get("timestamp"),
                "symbol": response.get("symbol"),
                "status": response.get("status"),
                "provider": "polygon",
            }
            logger.info("Polygon API request successful")
            return result
        except Exception as e:
            logger.exception(f"Error fetching conversion from Polygon: {e}")
            raise e
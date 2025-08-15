# Rate processor service
"""
This service is responsible for processing and aggregating forex rates from various providers.
"""

from loguru import logger

from app.models import CurrencyPair
from app.services.rate_fetcher import RateFetcherService


class RateProcessorService:
    def __init__(self):
        self.rate_fetcher = RateFetcherService()

    def process_rates_for_currencies(self):
        """
        Fetch rates for a specific currency pair from providers, clean the results, and save to the database.
        """
        # fetch the currencies
        currencies = self._get_currencies()

        provider_results = []
        # fetch rate from exchange rates api
        exchange_rates_api_results = self._process_exchange_rate_client(currencies)

        provider_results.append(
            {"source": "exchange_rates_api", "data": exchange_rates_api_results}
        )

        # Clean and save rates to the database
        self._save_rates(currencies, provider_results)

        # Perform aggregation
        self._aggregate_rates(currencies, provider_results)

    def _get_currencies(self):
        """
        Fetch currency pairs from the database and process rates for each pair.
        """
        currency_pairs = CurrencyPair.query.filter_by(is_active=True).all()

        return currency_pairs

    def _group_currency_pairs_by_base(self, currency_pairs):
        """
        Group currency pairs by base currency for rate fetching - [USD, ZAR]
        Returns:
            grouped (dict): Dictionary of grouped currency pairs by base currency.

        {
        "USD": ["GBP", "ZAR"],
        "ZAR": ["GBP"]
        }
        """
        logger.debug("Grouping currency pairs by base currency.")
        grouped = {}

        for pair in currency_pairs:
            if pair.base_currency not in grouped:
                grouped[pair.base_currency] = []
            grouped[pair.base_currency].append(pair.target_currency)

        logger.debug(f"Grouped currency pairs: {grouped}")
        return grouped

    def _process_exchange_rate_client(self, currencies) -> dict:
        """
        Process rates for Exchange Rate API.

        result:
        {
            "USD": [ {
                "pair" : "ZAR",
                "rate": "<rate>",
                "fetched_at": "<last_update_utc_from_provider>"
                },
                {
                "pair" : "GBP",
                "rate": "<rate>",
                "fetched_at": "<last_update_utc_from_provider>"
                }
            ]
        }
        """
        logger.debug("Processing rates using Exchange Rate API.")
        grouped_currency_pairs = self._group_currency_pairs_by_base(currencies)
        logger.debug(
            f"Grouped currency pairs for Exchange Rate API: {grouped_currency_pairs}"
        )

        # process rates for each base currency
        results = {}
        for base_currency, target_currencies in grouped_currency_pairs.items():
            logger.info(
                f"Fetching rates for base currency {base_currency} using ExchangeRateClient"
            )
            rates = self.rate_fetcher.fetch_rates(
                provider_name="exchange_rate", base_currency=base_currency
            )
            logger.debug(f"Fetched rates for base currency {base_currency}: {rates}")

            # extract rate for each target currency
            results[base_currency] = []
            for target_currency in target_currencies:
                if target_currency in rates["conversion_rates"]:
                    results[base_currency].append(
                        {
                            "pair": target_currency,
                            "rate": rates["conversion_rates"][target_currency],
                            "fetched_at": rates["last_update_utc"],
                        }
                    )
                    logger.debug(
                        f"Mapped rate for {base_currency}-{target_currency}: {rates['conversion_rates'][target_currency]}"
                    )
                else:
                    logger.warning(
                        f"Rate for {base_currency}-{target_currency} not found in ExchangeRateClient response."
                    )

        logger.debug(f"Processed Exchange Rate API results: {results}")
        return results

    def _save_rates(self, provider_results):
        """
        Save cleaned rates to the database.
        """
        # Skeleton logic for saving rates
        pass

    def _aggregate_rates(self, currency_pair):
        """
        Aggregate rates for the currency pair and save to the aggregation table.
        """
        # Skeleton logic for aggregation
        pass

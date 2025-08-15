# Rate processor service
"""
This service is responsible for processing and aggregating forex rates from various providers.
"""

from datetime import timedelta

from loguru import logger
from sqlalchemy import func

from app import db
from app.models import AggregatedRate, CurrencyPair, Rate
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

        # fetch rate from polygon api
        polygon_results = self._process_polygon_client(currencies)

        provider_results.append(
            {"source": "exchange_rates_api", "rate_data": exchange_rates_api_results},
            {"source": "polygon", "rate_data": polygon_results},
        )

        # Clean and save rates to the database
        self._save_rates(currencies, provider_results)

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
            rate_data = self.rate_fetcher.fetch_rates(
                provider_name="exchange_rate", base_currency=base_currency
            )
            logger.debug(
                f"Fetched rates for base currency {base_currency}: {rate_data}"
            )

            # extract rate for each target currency
            results[base_currency] = []
            for target_currency in target_currencies:
                if target_currency in rate_data["conversion_rates"]:
                    results[base_currency].append(
                        {
                            "pair": target_currency,
                            "rate": rate_data["conversion_rates"][target_currency],
                            "fetched_at": rate_data["last_update_utc"],
                        }
                    )
                    logger.debug(
                        f"Mapped rate for {base_currency}-{target_currency}: {rate_data['conversion_rates'][target_currency]}"
                    )
                else:
                    logger.warning(
                        f"Rate for {base_currency}-{target_currency} not found in ExchangeRateClient response."
                    )

        logger.debug(f"Processed Exchange Rate API results: {results}")
        return results

    def _process_polygon_client(self, currencies) -> dict:
        """
        Process rates for Polygon API.

        result:
        {
            "USD": [
                {
                    "pair": "ZAR",
                    "rate": "<rate>",
                    "fetched_at": "<timestamp_from_provider>"
                },
                {
                    "pair": "GBP",
                    "rate": "<rate>",
                    "fetched_at": "<timestamp_from_provider>"
                }
            ]
        }
        """
        logger.debug("Processing rates using Polygon API.")
        results = {}

        for currency_pair in currencies:
            base_currency = currency_pair.base_currency
            target_currency = currency_pair.target_currency

            logger.info(
                f"Fetching rate for {base_currency}-{target_currency} using PolygonClient"
            )
            try:
                rate_data = self.rate_fetcher.fetch_rates(
                    provider_name="polygon",
                    from_currency=base_currency,
                    to_currency=target_currency,
                )
                logger.debug(
                    f"Fetched rate for {base_currency}-{target_currency}: {rate_data}"
                )

                if base_currency not in results:
                    results[base_currency] = []

                results[base_currency].append(
                    {
                        "pair": target_currency,
                        "rate": rate_data["conversion_rate"],
                        "fetched_at": rate_data["last_update_utc"],
                    }
                )
            except Exception as e:
                logger.error(
                    f"Failed to fetch rate for {base_currency}-{target_currency} using PolygonClient: {e}"
                )

        logger.debug(f"Processed Polygon API results: {results}")
        return results

    def _save_rates(self, currencies: list[CurrencyPair], provider_results: list[dict]):
        """
        Save cleaned rates to the database.
        Args:
            currencies (list): List of CurrencyPair objects.
            provider_results (list): List of provider results containing rate data.
        """
        logger.debug("Saving rates to the database.")

        try:
            for provider_result in provider_results:
                source = provider_result["source"]
                rate_data = provider_result["rate_data"]

                for base_currency, rates in rate_data.items():
                    rates_to_aggregate = []
                    for rate in rates:
                        # Find the corresponding currency pair
                        currency_pair = next(
                            (
                                pair
                                for pair in currencies
                                if pair.base_currency == base_currency
                                and pair.target_currency == rate["pair"]
                            ),
                            None,
                        )

                        if not currency_pair:
                            logger.warning(
                                f"Currency pair {base_currency}-{rate['pair']} not found in the database."
                            )
                            continue

                        # Create a new Rate object
                        new_rate = Rate(
                            currency_pair_id=currency_pair.id,
                            # provider_id=source,  # no provider id at the moment
                            buy_rate=rate["rate"],
                            sell_rate=rate["rate"],
                            fetched_at=rate["fetched_at"],
                            created_at=func.now(),
                        )

                        rates_to_aggregate.append(new_rate)

                        # Save to the database
                        db.session.add(new_rate)
                        logger.info(
                            f"Saved rate for {base_currency}-{rate['pair']} from {source}."
                        )

                    # Aggregate rates for the currency pair
                    self._aggregate_rates(rates_to_aggregate, len(provider_results))

            # Commit the transaction
            db.session.commit()
            logger.debug("Rates successfully saved to the database.")

        except Exception as e:
            logger.error(f"Failed to save rates to the database: {e}")
            db.session.rollback()

    def _aggregate_rates(self, rates: list[Rate], provider_count: int):
        """
        Aggregate rates for the currency pair and save to the aggregation table.
        """
        if not rates:
            logger.warning("No rates available for aggregation.")
            return

        currency_pair = rates[0].currency_pair

        logger.debug(
            f"Aggregating rates for currency pair {currency_pair.base_currency}-{currency_pair.target_currency}."
        )

        # Calculate average buy and sell rates
        average_buy_rate = sum(rate.buy_rate for rate in rates) / len(rates)
        average_sell_rate = sum(rate.sell_rate for rate in rates) / len(rates)

        # Apply markup
        final_buy_rate = average_buy_rate * (1 + currency_pair.markup_percentage)
        final_sell_rate = average_sell_rate * (1 - currency_pair.markup_percentage)

        # Create a new AggregatedRate object
        aggregated_rate = AggregatedRate(
            currency_pair_id=currency_pair.id,
            average_buy_rate=average_buy_rate,
            average_sell_rate=average_sell_rate,
            final_buy_rate=final_buy_rate,
            final_sell_rate=final_sell_rate,
            markup_percentage=currency_pair.markup_percentage,
            provider_count=provider_count,
            aggregated_at=func.now(),
            expires_at=func.now() + timedelta(hours=1),
            created_at=func.now(),
        )

        # Save to the database
        db.session.add(aggregated_rate)
        logger.info(
            f"Aggregated rates saved for currency pair {currency_pair.base_currency}-{currency_pair.target_currency}."
        )

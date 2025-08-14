

import concurrent.futures
import time

from loguru import logger

from app.services.providers.provider_factory import (
	PROVIDER_CLIENTS,
	get_provider_client,
)


def exponential_backoff(attempt, base=0.5, factor=2.0, max_backoff=8.0):
	return min(base * (factor ** (attempt - 1)), max_backoff)

class RateFetcherService:
	def __init__(self, provider_names=None):

		if provider_names is None:
			provider_names = list(PROVIDER_CLIENTS.keys())

		self.provider_names = provider_names
		self.providers = [get_provider_client(name) for name in provider_names]

	def fetch_rates(self, *args, **kwargs):
		"""
		Fetch rates concurrently from all configured providers with retry, failover, and validation.
		Returns the first successful, validated response or raises an error if all fail.
		"""
		errors = []
		with concurrent.futures.ThreadPoolExecutor() as executor:
			future_to_provider = {
				executor.submit(self._fetch_with_retry, provider, *args, **kwargs): provider
				for provider in self.providers
			}

			for future in concurrent.futures.as_completed(future_to_provider):
				provider = future_to_provider[future]
				try:
					result = future.result()
					if result and self._validate_rate_data(result):
						logger.info(f"Valid rates received from {provider.__class__.__name__}")
						return result
					else:
						logger.warning(f"Invalid or empty rates from {provider.__class__.__name__}")
						errors.append(f"Invalid/empty rates from {provider.__class__.__name__}")
				except Exception as e:
					logger.error(f"Error fetching rates from {provider.__class__.__name__}: {e}")
					errors.append(str(e))
		logger.error(f"All providers failed. Errors: {errors}")
		raise Exception(f"All providers failed. Errors: {errors}")

	def _fetch_with_retry(self, provider, *args, **kwargs):
		max_attempts = getattr(provider, 'max_retries', 3)
		for attempt in range(1, max_attempts + 1):
			try:
				logger.info(f"Attempt {attempt}: Fetching rates from {provider.__class__.__name__}")
				return provider.get_rates(*args, **kwargs)
			except Exception as e:
				logger.warning(f"Attempt {attempt} failed for {provider.__class__.__name__}: {e}")
				if attempt == max_attempts:
					raise
				backoff = exponential_backoff(attempt)
				logger.info(f"Backing off for {backoff} seconds before retrying {provider.__class__.__name__}")
				time.sleep(backoff)

	def _validate_rate_data(self, data):
		# Basic validation: check for required keys and non-empty values
		required_keys = ["base_code", "conversion_rates"]
		if not isinstance(data, dict):
			return False
		for key in required_keys:
			if key not in data or not data[key]:
				return False
		return True

    # add sanitazation of the results

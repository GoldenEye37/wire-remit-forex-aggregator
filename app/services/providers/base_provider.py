import abc
from typing import Any

from loguru import logger


# TODO: Implement inheritance of the fetch with retry for all provider clients
class BaseProviderClient(abc.ABC):
    """
    Abstract base class for all provider clients.
    """

    timeout: int = 10
    max_retries: int = 3

    def __init__(self):
        self.circuit_open = False
        self.failure_count = 0
        self.circuit_breaker_threshold = 3

    @abc.abstractmethod
    def get_rates(self, *args, **kwargs) -> dict[str, Any]:
        pass

    @abc.abstractmethod
    def health_check(self) -> dict[str, Any]:
        pass

    def request_with_retry(self, func, *args, **kwargs):
        """
        Retry logic for API requests.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                if self.circuit_open:
                    logger.error(f"Circuit breaker open for {self.__class__.__name__}")
                    raise Exception("Circuit breaker is open.")
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Attempt {attempt} failed: {e}")
                self.failure_count += 1
                if self.failure_count >= self.circuit_breaker_threshold:
                    self.circuit_open = True
                    logger.error(
                        f"Circuit breaker triggered for {self.__class__.__name__}"
                    )
                if attempt == self.max_retries:
                    raise

    def reset_circuit(self):
        self.circuit_open = False
        self.failure_count = 0

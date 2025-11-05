import concurrent.futures
import time

from opentelemetry import trace

from app.services.providers.provider_factory import (
    PROVIDER_CLIENTS,
    get_provider_client,
)
from app.utils.logging import log_provider_operation, logger
from app.utils.metrics import record_rate_fetch_metrics
from app.utils.tracing import (
    add_span_attributes,
    add_span_event,
    trace_currency_pair,
    with_span,
)


def exponential_backoff(attempt, base=0.5, factor=2.0, max_backoff=8.0):
    return min(base * (factor ** (attempt - 1)), max_backoff)


class RateFetcherService:
    def __init__(self, provider_names=None):
        if provider_names is None:
            provider_names = list(PROVIDER_CLIENTS.keys())

        self.provider_names = provider_names
        self.providers = [get_provider_client(name) for name in provider_names]

    @with_span("rate_fetcher.fetch_rates")
    def fetch_rates(self, *args, **kwargs):
        """
        Fetch rates concurrently from all configured providers with retry, failover, and validation.
        Returns the first successful, validated response or raises an error if all fail.
        """
        span = trace.get_current_span()

        # Add currency context to span
        base_currency = kwargs.get("base_currency") or (args[0] if args else None)
        target_currency = kwargs.get("target_currency") or (
            args[1] if len(args) > 1 else None
        )

        if base_currency:
            trace_currency_pair(span, base_currency, target_currency)

        # Add provider information
        add_span_attributes(
            span,
            {
                "provider.count": len(self.providers),
                "provider.names": ",".join(
                    [p.__class__.__name__ for p in self.providers]
                ),
                "operation.type": "fetch_concurrent",
            },
        )

        errors = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_provider = {
                executor.submit(
                    self._fetch_with_retry, provider, *args, **kwargs
                ): provider
                for provider in self.providers
            }

            add_span_event(
                span, "providers_submitted", {"provider.count": len(future_to_provider)}
            )

            for future in concurrent.futures.as_completed(future_to_provider):
                provider = future_to_provider[future]
                provider_name = provider.__class__.__name__
                start_time = time.time()

                try:
                    result = future.result()
                    duration_ms = (time.time() - start_time) * 1000

                    if result and self._validate_rate_data(result):
                        rate_count = len(result.get("conversion_rates", {}))
                        log_provider_operation(
                            provider_name,
                            "fetch_rates",
                            success=True,
                            duration_ms=duration_ms,
                            rate_count=rate_count,
                            base_currency=base_currency,
                        )
                        record_rate_fetch_metrics(
                            provider_name, success=True, duration_ms=duration_ms
                        )

                        # Add success event and attributes
                        add_span_event(
                            span,
                            "provider_success",
                            {
                                "provider.name": provider_name,
                                "provider.duration_ms": round(duration_ms, 2),
                            },
                        )
                        add_span_attributes(
                            span,
                            {
                                "provider.success": provider_name,
                                "rate.count": rate_count,
                            },
                        )

                        return result
                    else:
                        log_provider_operation(
                            provider_name,
                            "fetch_rates",
                            success=False,
                            duration_ms=duration_ms,
                            error_type="invalid_data",
                        )
                        record_rate_fetch_metrics(
                            provider_name,
                            success=False,
                            duration_ms=duration_ms,
                            error_type="invalid_data",
                        )
                        add_span_event(
                            span,
                            "provider_validation_failed",
                            {"provider.name": provider_name},
                        )
                        errors.append(f"Invalid/empty rates from {provider_name}")
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    error_type = type(e).__name__
                    log_provider_operation(
                        provider_name,
                        "fetch_rates",
                        success=False,
                        duration_ms=duration_ms,
                        error_type=error_type,
                        error_message=str(e),
                    )
                    record_rate_fetch_metrics(
                        provider_name,
                        success=False,
                        duration_ms=duration_ms,
                        error_type=error_type,
                    )
                    add_span_event(
                        span,
                        "provider_error",
                        {
                            "provider.name": provider_name,
                            "error.type": error_type,
                            "error.message": str(e),
                        },
                    )
                    errors.append(str(e))

        # All providers failed
        logger.error(
            "All providers failed",
            provider_count=len(self.providers),
            error_count=len(errors),
            base_currency=base_currency,
        )
        add_span_attributes(
            span, {"operation.success": False, "error.count": len(errors)}
        )
        raise Exception(f"All providers failed. Errors: {errors}")

    @with_span("rate_fetcher.fetch_with_retry")
    def _fetch_with_retry(self, provider, *args, **kwargs):
        span = trace.get_current_span()
        provider_name = provider.__class__.__name__
        max_attempts = getattr(provider, "max_retries", 3)

        # Add provider and retry context
        add_span_attributes(
            span,
            {
                "provider.name": provider_name,
                "retry.max_attempts": max_attempts,
                "operation.type": "fetch_with_retry",
            },
        )

        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Attempt {attempt}: Fetching rates from {provider_name}")

                add_span_event(
                    span,
                    "retry_attempt",
                    {"retry.attempt": attempt, "provider.name": provider_name},
                )

                result = provider.get_rates(*args, **kwargs)

                # Success on this attempt
                add_span_attributes(
                    span, {"retry.success_attempt": attempt, "operation.success": True}
                )

                return result
            except Exception as e:
                logger.warning(f"Attempt {attempt} failed for {provider_name}: {e}")

                add_span_event(
                    span,
                    "retry_failed",
                    {
                        "retry.attempt": attempt,
                        "provider.name": provider_name,
                        "error.type": type(e).__name__,
                        "error.message": str(e),
                    },
                )

                if attempt == max_attempts:
                    # Final attempt failed
                    add_span_attributes(
                        span, {"retry.exhausted": True, "operation.success": False}
                    )
                    raise

                backoff = exponential_backoff(attempt)
                logger.info(
                    f"Backing off for {backoff} seconds before retrying {provider_name}"
                )

                add_span_event(
                    span,
                    "retry_backoff",
                    {
                        "backoff.duration_seconds": backoff,
                        "retry.next_attempt": attempt + 1,
                    },
                )

                time.sleep(backoff)

    @with_span("rate_fetcher.validate_rate_data")
    def _validate_rate_data(self, data):
        span = trace.get_current_span()

        # Basic validation: check for required keys and non-empty values
        required_keys = ["base_code", "conversion_rates"]

        add_span_attributes(
            span,
            {
                "validation.required_keys": ",".join(required_keys),
                "data.type": type(data).__name__,
            },
        )

        if not isinstance(data, dict):
            add_span_attributes(
                span, {"validation.result": False, "validation.reason": "data_not_dict"}
            )
            return False

        for key in required_keys:
            if key not in data or not data[key]:
                add_span_attributes(
                    span,
                    {
                        "validation.result": False,
                        "validation.reason": f"missing_or_empty_{key}",
                    },
                )
                return False

        # Validation successful
        add_span_attributes(
            span,
            {
                "validation.result": True,
                "rate.count": len(data.get("conversion_rates", {})),
                "currency.base": data.get("base_code"),
            },
        )
        return True

        # add sanitazation of the results

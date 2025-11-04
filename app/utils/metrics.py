"""
Utility functions for recording custom OpenTelemetry metrics.

This module provides helper functions and decorators to easily record
metrics throughout the application without cluttering business logic.
"""

from flask import current_app, request
from functools import wraps
from typing import Optional
import time

from loguru import logger


def record_request_metrics(
    endpoint: str, method: str, status_code: int, duration_ms: float
) -> None:
    """
    Record HTTP request metrics.

    Args:
        endpoint: The API endpoint (e.g., "/api/v1.0/rates")
        method: HTTP method (GET, POST, etc.)
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
    """
    if not hasattr(current_app, "custom_metrics"):
        return

    metrics = current_app.custom_metrics

    # Record request count
    if "api_requests_total" in metrics:
        metrics["api_requests_total"].add(
            1,
            {
                "endpoint": endpoint,
                "method": method,
                "status": str(status_code),
            },
        )

    # Record request duration
    if "request_duration" in metrics:
        status_category = "success" if status_code < 400 else "error"
        metrics["request_duration"].record(
            duration_ms,
            {
                "endpoint": endpoint,
                "status": status_category,
            },
        )


def record_rate_fetch_metrics(
    provider: str,
    success: bool,
    duration_ms: Optional[float] = None,
    error_type: Optional[str] = None,
) -> None:
    """
    Record rate fetching metrics.

    Args:
        provider: Provider name (e.g., "ExchangeRateClient")
        success: Whether the fetch was successful
        duration_ms: Optional fetch duration in milliseconds
        error_type: Optional error type if fetch failed
    """
    if not hasattr(current_app, "custom_metrics"):
        return

    metrics = current_app.custom_metrics

    # Record fetch attempt
    if "rate_fetches_total" in metrics:
        metrics["rate_fetches_total"].add(
            1,
            {
                "provider": provider,
                "status": "success" if success else "failure",
            },
        )

    # Record fetch duration if provided
    if duration_ms and "request_duration" in metrics:
        metrics["request_duration"].record(
            duration_ms,
            {
                "endpoint": f"/fetch/{provider}",
                "status": "success" if success else "error",
            },
        )

    # Record error if fetch failed
    if not success and error_type:
        record_provider_error(provider, error_type)


def record_provider_error(provider: str, error_type: str) -> None:
    """
    Record provider error metrics.

    Args:
        provider: Provider name
        error_type: Type of error (e.g., "timeout", "invalid_data", "ConnectionError")
    """
    if not hasattr(current_app, "custom_metrics"):
        return

    metrics = current_app.custom_metrics

    if "provider_errors_total" in metrics:
        metrics["provider_errors_total"].add(
            1,
            {
                "provider": provider,
                "error_type": error_type,
            },
        )


def record_aggregation_metrics(
    currency_pair_count: int, duration_ms: float, success: bool = True
) -> None:
    """
    Record rate aggregation metrics.

    Args:
        currency_pair_count: Number of currency pairs processed
        duration_ms: Aggregation duration in milliseconds
        success: Whether aggregation was successful
    """
    if not hasattr(current_app, "custom_metrics"):
        return

    metrics = current_app.custom_metrics

    # Record aggregation count
    if "rate_fetches_total" in metrics:
        metrics["rate_fetches_total"].add(
            currency_pair_count,
            {
                "provider": "aggregator",
                "status": "success" if success else "failure",
            },
        )

    # Record aggregation duration
    if "request_duration" in metrics:
        metrics["request_duration"].record(
            duration_ms,
            {
                "endpoint": "/internal/aggregate_rates",
                "status": "success" if success else "error",
            },
        )


def record_cache_operation(operation: str, hit: bool = True) -> None:
    """
    Record cache operation metrics.

    Args:
        operation: Operation type (e.g., "get", "set", "delete")
        hit: Whether it was a cache hit (for get operations)
    """
    if not hasattr(current_app, "custom_metrics"):
        return

    metrics = current_app.custom_metrics

    if "cache_operations" in metrics:
        result = "hit" if hit else "miss"
        metrics["cache_operations"].add(
            1,
            {
                "operation": operation,
                "result": result,
            },
        )


def with_request_metrics(endpoint: str):
    """
    Decorator to automatically record request metrics.

    Wraps a Flask route handler to automatically track request count,
    duration, and status code.

    Usage:
        @rates_bp.route("/rates", methods=["GET"])
        @require_jwt
        @with_request_metrics("/api/v1.0/rates")
        def get_rates():
            return jsonify({"rates": []})

    Args:
        endpoint: The endpoint path for labeling metrics

    Returns:
        Decorated function that records metrics
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            status_code = 500  # Default to error if exception occurs

            try:
                response = f(*args, **kwargs)

                # Extract status code from response
                if isinstance(response, tuple):
                    status_code = response[1] if len(response) > 1 else 200
                else:
                    status_code = 200

                return response

            except Exception as e:
                # Re-raise the exception after recording metrics
                raise

            finally:
                # Always record metrics, even if an exception occurred
                try:
                    duration_ms = (time.time() - start_time) * 1000
                    record_request_metrics(
                        endpoint=endpoint,
                        method=request.method,
                        status_code=status_code,
                        duration_ms=duration_ms,
                    )
                except Exception as metric_error:
                    # Don't let metrics recording break the application
                    logger.warning(f"Failed to record metrics: {metric_error}")

        return decorated_function

    return decorator


def with_rate_fetch_metrics(provider_name: str):
    """
    Decorator to automatically record rate fetching metrics.

    Usage:
        @with_rate_fetch_metrics("ExchangeRateClient")
        def fetch_from_provider():
            return {"rates": {...}}

    Args:
        provider_name: Name of the rate provider

    Returns:
        Decorated function that records fetch metrics
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()

            try:
                result = f(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                # Record successful fetch
                record_rate_fetch_metrics(
                    provider=provider_name, success=True, duration_ms=duration_ms
                )

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                error_type = type(e).__name__

                # Record failed fetch
                record_rate_fetch_metrics(
                    provider=provider_name,
                    success=False,
                    duration_ms=duration_ms,
                    error_type=error_type,
                )

                raise

        return decorated_function

    return decorator

"""
Tracing utility module for WireRemit Forex Aggregator.

This module provides helper functions and decorators for creating custom spans
and adding business context to distributed traces.

Usage:
    from app.utils.tracing import with_span, add_span_attributes

    @with_span("my_operation")
    def my_function():
        span = trace.get_current_span()
        add_span_attributes(span, {"key": "value"})
        # Your code here
"""

import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import current_app, has_app_context
from opentelemetry import trace
from opentelemetry.trace import Span, Status, StatusCode


def get_tracer() -> trace.Tracer:
    """
    Get the application tracer instance.

    Returns:
        Tracer instance from Flask app or default tracer
    """
    if (
        has_app_context()
        and hasattr(current_app, "tracer")
        and current_app.tracer is not None
    ):
        return current_app.tracer
    return trace.get_tracer(__name__)


def add_span_attributes(span: Span, attributes: dict[str, Any]) -> None:
    """
    Add multiple attributes to a span.

    Filters out None values and only sets attributes if span is recording.

    Args:
        span: OpenTelemetry span
        attributes: Dictionary of attributes to add
    """
    if not span or not span.is_recording():
        return

    # Filter out None values
    filtered_attrs = {k: v for k, v in attributes.items() if v is not None}

    for key, value in filtered_attrs.items():
        try:
            span.set_attribute(key, value)
        except Exception as e:
            # Don't let attribute setting failures break the application
            if has_app_context() and hasattr(current_app, "logger"):
                current_app.logger.debug(f"Failed to set span attribute {key}: {e}")


def record_span_error(
    span: Span,
    exception: Exception,
    additional_attributes: dict[str, Any] | None = None,
) -> None:
    """
    Record an exception in a span with error attributes.

    Args:
        span: OpenTelemetry span
        exception: Exception that occurred
        additional_attributes: Optional additional attributes to add
    """
    if not span or not span.is_recording():
        return

    # Set error status
    span.set_status(Status(StatusCode.ERROR, str(exception)))

    # Record exception event
    span.record_exception(exception)

    # Add error attributes
    error_attrs = {
        "error": True,
        "exception.type": type(exception).__name__,
        "exception.message": str(exception),
    }

    if additional_attributes:
        error_attrs.update(additional_attributes)

    add_span_attributes(span, error_attrs)


def with_span(span_name: str, attributes: dict[str, Any] | None = None):
    """
    Decorator to automatically create a span for a function.

    Usage:
        @with_span("my_operation", {"operation.type": "fetch"})
        def my_function(arg1, arg2):
            # Function code here
            return result

    Args:
        span_name: Name for the span
        attributes: Optional attributes to add to the span

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()

            with tracer.start_as_current_span(span_name) as span:
                # Add provided attributes
                if attributes:
                    add_span_attributes(span, attributes)

                # Add function name as attribute
                add_span_attributes(
                    span,
                    {
                        "code.function": func.__name__,
                        "code.namespace": func.__module__,
                    },
                )

                start_time = time.time()

                try:
                    result = func(*args, **kwargs)

                    # Record duration
                    duration_ms = (time.time() - start_time) * 1000
                    add_span_attributes(
                        span, {"operation.duration_ms": round(duration_ms, 2)}
                    )

                    # Set success status
                    span.set_status(Status(StatusCode.OK))

                    return result

                except Exception as e:
                    # Record error
                    duration_ms = (time.time() - start_time) * 1000
                    record_span_error(
                        span, e, {"operation.duration_ms": round(duration_ms, 2)}
                    )
                    raise

        return wrapper

    return decorator


def with_provider_span(operation: str = "fetch_rates"):
    """
    Decorator to create a span for provider operations.

    Expects the decorated function to be a method with 'self' having
    a __class__.__name__ attribute for the provider name.

    Usage:
        @with_provider_span("fetch_rates")
        def fetch_rates(self, base_currency):
            # Provider code here
            return rates

    Args:
        operation: Operation name (default: "fetch_rates")

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            tracer = get_tracer()

            provider_name = self.__class__.__name__
            span_name = f"provider.{operation}"

            with tracer.start_as_current_span(span_name) as span:
                # Add provider-specific attributes
                add_span_attributes(
                    span,
                    {
                        "provider.name": provider_name,
                        "provider.operation": operation,
                        "code.function": func.__name__,
                    },
                )

                # Add priority if available
                if hasattr(self, "priority"):
                    add_span_attributes(span, {"provider.priority": self.priority})

                start_time = time.time()

                try:
                    result = func(self, *args, **kwargs)

                    # Record duration and success
                    duration_ms = (time.time() - start_time) * 1000
                    add_span_attributes(
                        span,
                        {
                            "operation.duration_ms": round(duration_ms, 2),
                            "operation.success": True,
                        },
                    )

                    # Add result count if applicable
                    if isinstance(result, dict) and "rates" in result:
                        add_span_attributes(span, {"rate.count": len(result["rates"])})

                    span.set_status(Status(StatusCode.OK))

                    return result

                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    record_span_error(
                        span,
                        e,
                        {
                            "operation.duration_ms": round(duration_ms, 2),
                            "operation.success": False,
                            "provider.name": provider_name,
                        },
                    )
                    raise

        return wrapper

    return decorator


def with_auth_span(auth_type: str = "jwt"):
    """
    Decorator to create a span for authentication operations.

    Usage:
        @with_auth_span("jwt")
        def require_jwt(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Auth code here
                return f(*args, **kwargs)
            return decorated_function

    Args:
        auth_type: Type of authentication (default: "jwt")

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()

            span_name = f"auth.validate_{auth_type}"

            with tracer.start_as_current_span(span_name) as span:
                add_span_attributes(
                    span,
                    {
                        "auth.type": auth_type,
                        "code.function": func.__name__,
                    },
                )

                start_time = time.time()

                try:
                    result = func(*args, **kwargs)

                    # Record success
                    duration_ms = (time.time() - start_time) * 1000
                    add_span_attributes(
                        span,
                        {
                            "auth.result": "success",
                            "operation.duration_ms": round(duration_ms, 2),
                        },
                    )

                    span.set_status(Status(StatusCode.OK))

                    return result

                except Exception as e:
                    # Record failure
                    duration_ms = (time.time() - start_time) * 1000
                    record_span_error(
                        span,
                        e,
                        {
                            "auth.result": "failure",
                            "operation.duration_ms": round(duration_ms, 2),
                        },
                    )
                    raise

        return wrapper

    return decorator


def create_manual_span(span_name: str, attributes: dict[str, Any] | None = None):
    """
    Create a manual span that must be explicitly closed.

    Use this for cases where you can't use a context manager or decorator.
    Remember to call span.end() when done!

    Usage:
        span = create_manual_span("my_operation", {"key": "value"})
        try:
            # Your code here
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            record_span_error(span, e)
        finally:
            span.end()

    Args:
        span_name: Name for the span
        attributes: Optional attributes to add

    Returns:
        Started span (must be manually ended)
    """
    tracer = get_tracer()
    span = tracer.start_span(span_name)

    if attributes:
        add_span_attributes(span, attributes)

    return span


def add_span_event(
    span: Span, event_name: str, attributes: dict[str, Any] | None = None
) -> None:
    """
    Add an event to a span with optional attributes.

    Events are timestamped log messages within a span.

    Args:
        span: OpenTelemetry span
        event_name: Name of the event
        attributes: Optional event attributes
    """
    if not span or not span.is_recording():
        return

    if attributes:
        filtered_attrs = {k: v for k, v in attributes.items() if v is not None}
        span.add_event(event_name, attributes=filtered_attrs)
    else:
        span.add_event(event_name)


def trace_currency_pair(span: Span, base: str, target: str | None = None) -> None:
    """
    Add currency pair attributes to a span.

    Args:
        span: OpenTelemetry span
        base: Base currency code
        target: Target currency code (optional)
    """
    attributes = {"currency.base": base}

    if target:
        attributes["currency.target"] = target
        attributes["currency.pair"] = f"{base}/{target}"
    else:
        attributes["currency.target"] = "all"

    add_span_attributes(span, attributes)


def trace_user_context(
    span: Span, user_id: int | None = None, role: str | None = None
) -> None:
    """
    Add user context attributes to a span.

    Args:
        span: OpenTelemetry span
        user_id: User database ID
        role: User role (e.g., "admin", "user")
    """
    attributes = {}

    if user_id is not None:
        attributes["user.id"] = user_id

    if role:
        attributes["user.role"] = role

    if attributes:
        add_span_attributes(span, attributes)


def trace_operation_result(
    span: Span,
    success: bool,
    result_count: int | None = None,
    error_message: str | None = None,
) -> None:
    """
    Add operation result attributes to a span.

    Args:
        span: OpenTelemetry span
        success: Whether operation succeeded
        result_count: Number of items in result (optional)
        error_message: Error message if failed (optional)
    """
    attributes = {"operation.success": success}

    if result_count is not None:
        attributes["result.count"] = result_count

    if error_message:
        attributes["error.message"] = error_message

    add_span_attributes(span, attributes)

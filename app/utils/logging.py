"""
Structured logging configuration and utilities for the application.

This module provides:
- JSON structured logging with loguru
- Trace context correlation (trace_id, span_id)
- Request context injection
- Log level management
- Custom logging formatters
"""

import sys
from typing import Any

from flask import Flask, g, has_request_context, request
from loguru import logger
from opentelemetry import trace


def get_trace_context() -> dict[str, str]:
    """
    Extract current trace context from OpenTelemetry.

    Returns:
        Dictionary with trace_id and span_id if available, empty dict otherwise
    """
    context = {}

    try:
        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            span_context = span.get_span_context()
            # Format as hex strings (16 chars for trace_id, 16 chars for span_id)
            context["trace_id"] = format(span_context.trace_id, "032x")
            context["span_id"] = format(span_context.span_id, "016x")
    except Exception:
        # If tracing not initialized or error getting context, return empty dict
        pass

    return context


def get_request_context() -> dict[str, Any]:
    """
    Extract current request context from Flask.

    Returns:
        Dictionary with request information if in request context
    """
    context = {}

    if has_request_context():
        try:
            context["http.method"] = request.method
            context["http.path"] = request.path
            context["http.url"] = request.url

            # Add remote address if available
            if request.remote_addr:
                context["http.client_ip"] = request.remote_addr

            # Add user context if available in Flask g object
            if hasattr(g, "user_id"):
                context["user.id"] = g.user_id
            if hasattr(g, "user_role"):
                context["user.role"] = g.user_role

            # Add request ID if available
            if hasattr(g, "request_id"):
                context["request.id"] = g.request_id

        except Exception:
            # If any error extracting context, return what we have
            pass

    return context


def serialize_log_record(record: dict) -> dict:
    """
    Serialize a loguru record into a structured format with context.

    Args:
        record: Loguru record dictionary

    Returns:
        Serialized record with trace and request context
    """
    # Base log structure
    log_entry = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "logger": record["name"],
        "message": record["message"],
        "function": record["function"],
        "line": record["line"],
    }

    # Add trace context if available
    trace_context = get_trace_context()
    if trace_context:
        log_entry.update(trace_context)

    # Add request context if available
    request_context = get_request_context()
    if request_context:
        log_entry.update(request_context)

    # Add extra fields from record
    if record.get("extra"):
        # Filter out internal loguru fields
        extra = {k: v for k, v in record["extra"].items() if not k.startswith("_")}
        log_entry.update(extra)

    # Add exception info if present
    if record.get("exception"):
        exc_info = record["exception"]
        log_entry["exception"] = {
            "type": exc_info.type.__name__ if exc_info.type else None,
            "value": str(exc_info.value) if exc_info.value else None,
            "traceback": record.get("exception", {}).get("traceback", None),
        }

    return log_entry


def json_formatter(record: dict) -> str:
    """
    Format log record as JSON string.

    Args:
        record: Loguru record dictionary

    Returns:
        JSON formatted log string
    """
    import json

    serialized = serialize_log_record(record)
    return json.dumps(serialized) + "\n"


def console_formatter(record: dict) -> str:
    """
    Format log record for console output (human-readable with context).

    Args:
        record: Loguru record dictionary

    Returns:
        Formatted log string for console
    """
    trace_context = get_trace_context()
    trace_info = ""
    if trace_context:
        trace_info = f" [trace_id={trace_context.get('trace_id', '')[:8]}]"

    # Format: timestamp | LEVEL | message [trace_id=xxx] [context fields]
    base = (
        f"<green>{record['time']:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        f"<level>{record['level'].name:8}</level> | "
        f"<cyan>{record['name']}</cyan>:<cyan>{record['function']}</cyan>:"
        f"<cyan>{record['line']}</cyan> - "
        f"<level>{record['message']}</level>"
        f"{trace_info}"
    )

    # Add extra context if present
    if record.get("extra"):
        extra = {k: v for k, v in record["extra"].items() if not k.startswith("_")}
        if extra:
            extra_str = " | ".join([f"{k}={v}" for k, v in extra.items()])
            base += f" | {extra_str}"

    return base + "\n"


def setup_logging(app: Flask, log_level: str = "INFO", json_logs: bool = False):
    """
    Configure structured logging for the application.

    Args:
        app: Flask application instance
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: If True, output logs as JSON (for production),
                  otherwise use human-readable format (for development)
    """
    # Remove default loguru handler
    logger.remove()

    # Choose formatter based on environment
    formatter = json_formatter if json_logs else console_formatter

    # Add new handler with structured logging
    logger.add(
        sys.stderr,
        format=formatter,
        level=log_level,
        colorize=not json_logs,  # Only colorize in console mode
        backtrace=True,
        diagnose=True,
    )

    # Store logger configuration on app
    app.logger_configured = True
    app.log_level = log_level
    app.json_logs = json_logs

    logger.info(
        "Structured logging initialized",
        log_level=log_level,
        json_format=json_logs,
        service=app.config.get("OTEL_SERVICE_NAME", "forex-aggregator"),
    )


def log_with_context(level: str, message: str, **kwargs):
    """
    Log a message with automatic trace and request context.

    Args:
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        **kwargs: Additional context fields to include in log
    """
    log_func = getattr(logger, level.lower())
    log_func(message, **kwargs)


# Convenience functions
def log_request_start():
    """Log the start of a request with full context."""
    if has_request_context():
        logger.info(
            "Request started",
            http_method=request.method,
            http_path=request.path,
            http_query=request.query_string.decode() if request.query_string else None,
        )


def log_request_end(status_code: int, duration_ms: float):
    """
    Log the end of a request with status and duration.

    Args:
        status_code: HTTP response status code
        duration_ms: Request duration in milliseconds
    """
    if has_request_context():
        level = (
            "info" if status_code < 400 else "warning" if status_code < 500 else "error"
        )
        logger.log(
            level.upper(),
            "Request completed",
            http_method=request.method,
            http_path=request.path,
            http_status=status_code,
            duration_ms=round(duration_ms, 2),
        )


def log_business_event(event_type: str, **context):
    """
    Log a business event with context.

    Args:
        event_type: Type of business event (e.g., "rate_updated", "user_authenticated")
        **context: Event-specific context fields
    """
    logger.info(f"Business event: {event_type}", event_type=event_type, **context)


def log_error(error: Exception, message: str = "An error occurred", **context):
    """
    Log an error with exception details and context.

    Args:
        error: Exception instance
        message: Error message
        **context: Additional context fields
    """
    logger.error(
        message, error_type=type(error).__name__, error_message=str(error), **context
    )


def log_provider_operation(
    provider_name: str,
    operation: str,
    success: bool,
    duration_ms: float | None = None,
    **context,
):
    """
    Log a provider operation (fetch, validate, etc.).

    Args:
        provider_name: Name of the provider
        operation: Operation performed
        success: Whether operation succeeded
        duration_ms: Operation duration in milliseconds
        **context: Additional context fields
    """
    level = "info" if success else "warning"
    logger.log(
        level.upper(),
        f"Provider operation: {operation}",
        provider=provider_name,
        operation=operation,
        success=success,
        duration_ms=round(duration_ms, 2) if duration_ms else None,
        **context,
    )


def log_database_operation(
    operation: str,
    table: str,
    success: bool,
    duration_ms: float | None = None,
    **context,
):
    """
    Log a database operation.

    Args:
        operation: Database operation (SELECT, INSERT, UPDATE, DELETE)
        table: Table name
        success: Whether operation succeeded
        duration_ms: Operation duration in milliseconds
        **context: Additional context fields
    """
    level = "debug" if success else "error"
    logger.log(
        level.upper(),
        f"Database operation: {operation}",
        db_operation=operation,
        db_table=table,
        success=success,
        duration_ms=round(duration_ms, 2) if duration_ms else None,
        **context,
    )


def log_cache_operation(
    operation: str, key: str, hit: bool | None = None, **context
):
    """
    Log a cache operation.

    Args:
        operation: Cache operation (GET, SET, DELETE)
        key: Cache key
        hit: Whether it was a cache hit (for GET operations)
        **context: Additional context fields
    """
    logger.debug(
        f"Cache operation: {operation}",
        cache_operation=operation,
        cache_key=key,
        cache_hit=hit,
        **context,
    )


# Export the logger for direct use
__all__ = [
    "logger",
    "setup_logging",
    "log_with_context",
    "log_request_start",
    "log_request_end",
    "log_business_event",
    "log_error",
    "log_provider_operation",
    "log_database_operation",
    "log_cache_operation",
    "get_trace_context",
    "get_request_context",
]

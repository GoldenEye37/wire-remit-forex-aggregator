"""
Logging middleware for Flask application.

Provides:
- Automatic request/response logging
- Request timing
- Error logging
- Request ID generation and tracking
"""

import time
import uuid
from typing import Any

from flask import Flask, g, request
from loguru import logger


class LoggingMiddleware:
    """
    Middleware to log all requests and responses with timing information.
    """

    def __init__(self, app: Flask = None):
        """
        Initialize the logging middleware.

        Args:
            app: Flask application instance
        """
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        """
        Initialize the middleware with a Flask application.

        Args:
            app: Flask application instance
        """
        # Register before_request handler
        app.before_request(self.before_request)

        # Register after_request handler
        app.after_request(self.after_request)

        # Register teardown handler for errors
        app.teardown_request(self.teardown_request)

        logger.info("Logging middleware initialized")

    def before_request(self):
        """Handler called before each request."""
        # Generate unique request ID
        g.request_id = str(uuid.uuid4())

        # Record request start time
        g.request_start_time = time.time()

        # Extract user info if available (will be set by auth decorator)
        g.user_id = None
        g.user_role = None

        # Log request start
        logger.info(
            "Request started",
            request_id=g.request_id,
            http_method=request.method,
            http_path=request.path,
            http_url=request.url,
            http_query=request.query_string.decode() if request.query_string else None,
            http_client_ip=request.remote_addr,
            http_user_agent=request.headers.get("User-Agent", ""),
        )

    def after_request(self, response):
        """
        Handler called after each request.

        Args:
            response: Flask response object

        Returns:
            Modified response object
        """
        # Calculate request duration
        if hasattr(g, "request_start_time"):
            duration_ms = (time.time() - g.request_start_time) * 1000
        else:
            duration_ms = 0

        # Determine log level based on status code
        status_code = response.status_code
        if status_code < 400:
            log_level = "INFO"
        elif status_code < 500:
            log_level = "WARNING"
        else:
            log_level = "ERROR"

        # Build log context
        log_context = {
            "request_id": getattr(g, "request_id", None),
            "http_method": request.method,
            "http_path": request.path,
            "http_status": status_code,
            "duration_ms": round(duration_ms, 2),
            "response_size_bytes": response.content_length,
        }

        # Add user context if available
        if hasattr(g, "user_id") and g.user_id:
            log_context["user_id"] = g.user_id
        if hasattr(g, "user_role") and g.user_role:
            log_context["user_role"] = g.user_role

        # Log request completion
        logger.log(log_level, "Request completed", **log_context)

        # Add request ID to response headers for tracing
        response.headers["X-Request-ID"] = getattr(g, "request_id", "unknown")

        return response

    def teardown_request(self, exception: Any = None):
        """
        Handler called during request teardown (including errors).

        Args:
            exception: Exception that occurred during request processing, if any
        """
        if exception:
            # Calculate request duration
            if hasattr(g, "request_start_time"):
                duration_ms = (time.time() - g.request_start_time) * 1000
            else:
                duration_ms = 0

            # Log the error
            logger.error(
                "Request failed with exception",
                request_id=getattr(g, "request_id", None),
                http_method=request.method,
                http_path=request.path,
                duration_ms=round(duration_ms, 2),
                error_type=type(exception).__name__,
                error_message=str(exception),
                exc_info=True,
            )


def setup_logging_middleware(app: Flask):
    """
    Setup logging middleware for the application.

    Args:
        app: Flask application instance
    """
    middleware = LoggingMiddleware(app)
    return middleware

# Authorization decorators
import time
from functools import wraps

from flask import current_app, g, jsonify, request
from loguru import logger
from opentelemetry import trace

from app.services.auth_service import AuthService
from app.utils.tracing import (
    add_span_attributes,
    record_span_error,
    trace_user_context,
)


def _record_auth_metric(success: bool, duration_ms: float, auth_type: str = "jwt"):
    """Helper to record authentication metrics."""
    if not hasattr(current_app, "custom_metrics"):
        return

    metrics = current_app.custom_metrics

    # Use api_requests_total to track auth attempts
    if "api_requests_total" in metrics:
        metrics["api_requests_total"].add(
            1,
            {
                "endpoint": f"/auth/{auth_type}",
                "method": "VALIDATE",
                "status": "200" if success else "401",
            },
        )

    # Record auth duration
    if "request_duration" in metrics:
        metrics["request_duration"].record(
            duration_ms,
            {
                "endpoint": f"/auth/{auth_type}",
                "status": "success" if success else "error",
            },
        )


def require_jwt(f):
    """
    Decorator to require valid JWT authentication.
    Sets g.current_user for use in the endpoint.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        tracer = trace.get_tracer(__name__)

        with tracer.start_as_current_span("auth.validate_jwt") as span:
            start_time = time.time()

            add_span_attributes(
                span,
                {
                    "auth.type": "jwt",
                    "http.method": request.method,
                    "http.path": request.path,
                },
            )

            try:
                auth_header = request.headers.get("Authorization")
                if not auth_header or not auth_header.startswith("Bearer "):
                    duration_ms = (time.time() - start_time) * 1000
                    _record_auth_metric(success=False, duration_ms=duration_ms)

                    add_span_attributes(
                        span,
                        {
                            "auth.result": "failure",
                            "auth.failure_reason": "missing_token",
                        },
                    )

                    return jsonify({"error": "Authorization token required"}), 401

                token = auth_header.split(" ")[1]
                add_span_attributes(span, {"auth.token_present": True})

                auth_service = AuthService()
                user = auth_service.get_user_from_token(token)

                if not user:
                    duration_ms = (time.time() - start_time) * 1000
                    _record_auth_metric(success=False, duration_ms=duration_ms)

                    add_span_attributes(
                        span,
                        {
                            "auth.result": "failure",
                            "auth.failure_reason": "invalid_token",
                        },
                    )

                    return jsonify({"error": "Invalid or expired token"}), 401

                g.current_user = user

                duration_ms = (time.time() - start_time) * 1000
                _record_auth_metric(success=True, duration_ms=duration_ms)

                # Add user context to span
                trace_user_context(
                    span, user_id=user.id, role="admin" if user.is_admin else "user"
                )
                add_span_attributes(
                    span,
                    {
                        "auth.result": "success",
                        "operation.duration_ms": round(duration_ms, 2),
                    },
                )

                return f(*args, **kwargs)

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                _record_auth_metric(success=False, duration_ms=duration_ms)
                logger.error(f"JWT auth error: {e}")

                record_span_error(
                    span,
                    e,
                    {"auth.result": "failure", "auth.failure_reason": "exception"},
                )

                return jsonify({"error": "Authentication failed"}), 401

    return decorated_function


def require_admin(f):
    """
    Decorator to require admin authentication.
    Must be used after @require_jwt.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if not hasattr(g, "current_user") or not g.current_user:
                return jsonify({"error": "Authentication required"}), 401

            if not g.current_user.is_admin:
                return jsonify({"error": "Admin access required"}), 403

            return f(*args, **kwargs)

        except Exception as e:
            logger.error(f"Admin auth error: {e}")
            return jsonify({"error": "Authorization failed"}), 403

    return decorated_function


def require_jwt_admin(f):
    """
    Combined decorator that requires both JWT and admin privileges.
    Convenience decorator that combines @require_jwt and @require_admin.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        tracer = trace.get_tracer(__name__)

        with tracer.start_as_current_span("auth.validate_jwt_admin") as span:
            start_time = time.time()

            add_span_attributes(
                span,
                {
                    "auth.type": "admin",
                    "http.method": request.method,
                    "http.path": request.path,
                },
            )

            try:
                auth_header = request.headers.get("Authorization")
                if not auth_header or not auth_header.startswith("Bearer "):
                    duration_ms = (time.time() - start_time) * 1000
                    _record_auth_metric(
                        success=False, duration_ms=duration_ms, auth_type="admin"
                    )

                    add_span_attributes(
                        span,
                        {
                            "auth.result": "failure",
                            "auth.failure_reason": "missing_token",
                        },
                    )

                    return jsonify({"error": "Authorization token required"}), 401

                token = auth_header.split(" ")[1]
                add_span_attributes(span, {"auth.token_present": True})

                auth_service = AuthService()
                user = auth_service.get_user_from_token(token)

                if not user:
                    duration_ms = (time.time() - start_time) * 1000
                    _record_auth_metric(
                        success=False, duration_ms=duration_ms, auth_type="admin"
                    )

                    add_span_attributes(
                        span,
                        {
                            "auth.result": "failure",
                            "auth.failure_reason": "invalid_token",
                        },
                    )

                    return jsonify({"error": "Invalid or expired token"}), 401

                if not user.is_admin:
                    duration_ms = (time.time() - start_time) * 1000
                    _record_auth_metric(
                        success=False, duration_ms=duration_ms, auth_type="admin"
                    )

                    add_span_attributes(
                        span,
                        {
                            "auth.result": "failure",
                            "auth.failure_reason": "insufficient_privileges",
                        },
                    )
                    trace_user_context(span, user_id=user.id, role="user")

                    return jsonify({"error": "Admin access required"}), 403

                g.current_user = user

                duration_ms = (time.time() - start_time) * 1000
                _record_auth_metric(
                    success=True, duration_ms=duration_ms, auth_type="admin"
                )

                # Add user context to span
                trace_user_context(span, user_id=user.id, role="admin")
                add_span_attributes(
                    span,
                    {
                        "auth.result": "success",
                        "operation.duration_ms": round(duration_ms, 2),
                    },
                )

                return f(*args, **kwargs)

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                _record_auth_metric(
                    success=False, duration_ms=duration_ms, auth_type="admin"
                )
                logger.error(f"JWT admin auth error: {e}")

                record_span_error(
                    span,
                    e,
                    {"auth.result": "failure", "auth.failure_reason": "exception"},
                )

                return jsonify({"error": "Authentication failed"}), 401

    return decorated_function

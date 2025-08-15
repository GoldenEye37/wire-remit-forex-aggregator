# Authorization decorators
from functools import wraps

from flask import g, jsonify, request
from loguru import logger

from app.services.auth_service import AuthService


def require_jwt(f):
    """
    Decorator to require valid JWT authentication.
    Sets g.current_user for use in the endpoint.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify({"error": "Authorization token required"}), 401

            token = auth_header.split(" ")[1]

            auth_service = AuthService()
            user = auth_service.get_user_from_token(token)

            if not user:
                return jsonify({"error": "Invalid or expired token"}), 401

            g.current_user = user

            return f(*args, **kwargs)

        except Exception as e:
            logger.error(f"JWT auth error: {e}")
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
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify({"error": "Authorization token required"}), 401

            token = auth_header.split(" ")[1]

            auth_service = AuthService()
            user = auth_service.get_user_from_token(token)

            if not user:
                return jsonify({"error": "Invalid or expired token"}), 401

            if not user.is_admin:
                return jsonify({"error": "Admin access required"}), 403

            g.current_user = user

            return f(*args, **kwargs)

        except Exception as e:
            logger.error(f"JWT admin auth error: {e}")
            return jsonify({"error": "Authentication failed"}), 401

    return decorated_function

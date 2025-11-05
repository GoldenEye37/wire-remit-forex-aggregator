# Auth API
from flask import Blueprint, jsonify, request

from app.services.auth_service import AuthService
from app.utils.logging import log_business_event, log_error, logger
from app.utils.metrics import with_request_metrics

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/signup", methods=["POST"])
@with_request_metrics("/api/v1.0/auth/signup")
def register():
    """
    Register a new user.
    Expected JSON: {"email": "user@example.com", "password": "password", "password_confirmation": "password", "first_name": "John", "last_name": "Doe"}
    """
    try:
        data = request.get_json()

        logger.debug("User signup attempt", operation="signup")

        if not data or not data.get("email") or not data.get("password"):
            logger.warning("Signup failed: missing required fields", operation="signup")
            return jsonify({"error": "Email and password are required"}), 400

        password_confirmation = data.get("password_confirmation")
        if not password_confirmation:
            logger.warning(
                "Signup failed: missing password confirmation", operation="signup"
            )
            return jsonify({"error": "Password confirmation is required"}), 400

        email = data.get("email").strip().lower()
        password = data.get("password")
        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()

        if password != password_confirmation:
            logger.warning(
                "Signup failed: password mismatch", operation="signup", email=email
            )
            return jsonify({"error": "Passwords do not match"}), 400

        if not AuthService.validate_email_address(email):
            logger.warning(
                "Signup failed: invalid email format", operation="signup", email=email
            )
            return jsonify({"error": "Invalid email format"}), 400

        is_valid, error_message = AuthService.validate_password_strength(password)
        if not is_valid:
            logger.warning(
                "Signup failed: weak password", operation="signup", email=email
            )
            return jsonify({"error": error_message}), 400

        auth_service = AuthService()
        registration_result = auth_service.register_user(
            email, password, first_name, last_name
        )

        if registration_result["success"]:
            logger.info("User registered successfully", operation="signup", email=email)
            log_business_event(
                "user_registered", email=email, has_name=bool(first_name)
            )
            return jsonify(registration_result), 201
        else:
            logger.warning(
                "Registration failed",
                operation="signup",
                email=email,
                reason=registration_result["message"],
            )
            return jsonify({"error": registration_result["message"]}), 400

    except Exception as e:
        log_error(e, "Registration error", operation="signup")
        return jsonify({"error": "Registration failed"}), 500


@auth_bp.route("/login", methods=["POST"])
@with_request_metrics("/api/v1.0/auth/login")
def login():
    """
    Authenticate user login.
    Expected JSON: {"email": "user@example.com", "password": "password"}
    """
    try:
        data = request.get_json()

        logger.debug("User login attempt", operation="login")

        if not data or not data.get("email") or not data.get("password"):
            logger.warning("Login failed: missing credentials", operation="login")
            return jsonify({"error": "Email and password are required"}), 400

        email = data.get("email").strip().lower()
        password = data.get("password")

        # Login user
        auth_service = AuthService()
        login_result = auth_service.login_user(email, password)

        if login_result["success"]:
            logger.info("User logged in successfully", operation="login", email=email)
            log_business_event(
                "user_authenticated", email=email, auth_method="password"
            )
            return jsonify(login_result), 200
        else:
            logger.warning(
                "Login failed",
                operation="login",
                email=email,
                reason=login_result["message"],
            )
            log_business_event(
                "authentication_failed", email=email, reason=login_result["message"]
            )
            return jsonify({"error": login_result["message"]}), 401

    except Exception as e:
        log_error(e, "Login error", operation="login")
        return jsonify({"error": "Login failed"}), 500

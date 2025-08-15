# Auth API
from flask import Blueprint, jsonify, request
from loguru import logger

from app.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/signup", methods=["POST"])
def register():
    """
    Register a new user.
    Expected JSON: {"email": "user@example.com", "password": "password", "password_confirmation": "password", "first_name": "John", "last_name": "Doe"}
    """
    try:
        data = request.get_json()

        if not data or not data.get("email") or not data.get("password"):
            return jsonify({"error": "Email and password are required"}), 400

        password_confirmation = data.get("password_confirmation")
        if not password_confirmation:
            return jsonify({"error": "Password confirmation is required"}), 400

        email = data.get("email").strip().lower()
        password = data.get("password")
        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()

        if password != password_confirmation:
            return jsonify({"error": "Passwords do not match"}), 400

        if not AuthService.validate_email_address(email):
            return jsonify({"error": "Invalid email format"}), 400

        is_valid, error_message = AuthService.validate_password_strength(password)
        if not is_valid:
            return jsonify({"error": error_message}), 400

        auth_service = AuthService()
        registration_result = auth_service.register_user(
            email, password, first_name, last_name
        )

        if registration_result["success"]:
            return jsonify(registration_result), 201
        else:
            return jsonify({"error": registration_result["message"]}), 400

    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({"error": "Registration failed"}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Authenticate user login.
    Expected JSON: {"email": "user@example.com", "password": "password"}
    """
    try:
        data = request.get_json()

        if not data or not data.get("email") or not data.get("password"):
            return jsonify({"error": "Email and password are required"}), 400

        email = data.get("email").strip().lower()
        password = data.get("password")

        # Login user
        auth_service = AuthService()
        login_result = auth_service.login_user(email, password)

        if login_result["success"]:
            return jsonify(login_result), 200
        else:
            return jsonify({"error": login_result["message"]}), 401

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": "Login failed"}), 500

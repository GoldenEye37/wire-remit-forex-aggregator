# Admin API
from flask import Blueprint, jsonify, request
from loguru import logger

from app.services.currency_service import CurrencyService

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/", methods=["GET"])
def hello_admin():
    return "Hello, Admin!"


@admin_bp.route("/currency-pairs", methods=["POST"])
def add_currency_pair():
    """
    Add a new currency pair.
    Expected JSON: {
        "base_currency": "USD",
        "target_currency": "ZAR",
        "markup_percentage": 0.05,  # optional, default 0.1
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        base_currency = data.get('base_currency')
        target_currency = data.get('target_currency')

        if not base_currency or not target_currency:
            return jsonify({"error": "base_currency and target_currency are required"}), 400

        markup_percentage = data.get('markup_percentage', 0.1000)

        result = CurrencyService.add_currency_pair(
            base_currency=base_currency,
            target_currency=target_currency,
            markup_percentage=markup_percentage,
        )

        if result["success"]:
            return jsonify({
                "message": result["message"],
                "pair": result["pair"]
            }), 201
        else:
            return jsonify({"error": result["message"]}), 400

    except Exception as e:
        logger.error(f"Add currency pair error: {e}")
        return jsonify({"error": "Failed to add currency pair"}), 500


@admin_bp.route("/currency-pairs/markup", methods=["PUT"])
def update_all_pairs_markup():
    """
    Update markup for all currency pairs.
    Expected JSON: {"markup_percentage": 0.05}
    """
    try:
        data = request.get_json()

        if not data or 'markup_percentage' not in data:
            return jsonify({"error": "markup_percentage is required"}), 400

        markup_percentage = data.get('markup_percentage')

        if not isinstance(markup_percentage, int | float):
            return jsonify({"error": "markup_percentage must be a number"}), 400

        result = CurrencyService.update_all_pairs_markup(markup_percentage)

        if result["success"]:
            return jsonify({
                "message": result["message"],
                "updated_count": result["updated_count"],
                "new_markup": result["new_markup"]
            }), 200
        else:
            return jsonify({"error": result["message"]}), 400

    except Exception as e:
        logger.error(f"Update all pairs markup error: {e}")
        return jsonify({"error": "Failed to update markup for all pairs"}), 500


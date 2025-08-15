# Rates API
from flask import Blueprint, jsonify
from loguru import logger

from app.decorators import require_jwt
from app.models import AggregatedRate, CurrencyPair

rates_bp = Blueprint("rates", __name__, url_prefix="/rates")


@rates_bp.route("/", methods=["GET"])
@require_jwt
def get_rates():
    try:
        # Fetch all aggregated rates
        rates = AggregatedRate.get_all_latest()
        return jsonify([rate.to_dict_with_pair() for rate in rates])
    except Exception as e:
        logger.error(f"Error fetching rates: {e}")
        return jsonify({"error": "Internal Server Error"}), 500


@rates_bp.route("/rates/<string:base_or_target>", methods=["GET"])
@require_jwt
def get_rates_for_currency(base_or_target):
    try:
        error = CurrencyPair.validate_currency(base_or_target)
        if error:
            return jsonify({"error": error}), 400

        # Fetch rates for this currency
        rates = AggregatedRate.get_latest_for_currency(base_or_target)
        if not rates:
            return jsonify({}), 200

        return jsonify([rate.to_dict_with_pair() for rate in rates])
    except Exception as e:
        logger.error(f"Error fetching rates: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

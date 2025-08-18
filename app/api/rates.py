# Rates API
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from loguru import logger

from app.decorators import require_jwt
from app.extensions import db
from app.models import AggregatedRate, CurrencyPair

rates_bp = Blueprint("rates", __name__, url_prefix="/rates")


@rates_bp.route("", methods=["GET"])
@require_jwt
def get_rates():
    try:
        # Fetch all aggregated rates
        rates = AggregatedRate.get_latest_for_all()
        response = {
            "success": True,
            "data": rates
        }
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error fetching rates: {e}")
        return jsonify({"error": "Internal Server Error"}), 500


@rates_bp.route("/<string:base_or_target>", methods=["GET"])
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

        return jsonify(rates)
    except Exception as e:
        logger.error(f"Error fetching rates: {e}")
        return jsonify({"error": "Internal Server Error"}), 500


@rates_bp.route("/historical", methods=["GET"])
@require_jwt
def get_historical():
    """
    Get historical aggregated rates.
    Query params:
    - base: Base currency (optional)
    - target: Target currency (optional)
    - from_date: Start date (YYYY-MM-DD format, optional, default: 7 days ago)
    - to_date: End date (YYYY-MM-DD format, optional, default: today)
    - limit: Maximum number of records (optional, default: 100, max: 1000)
    - order: 'asc' or 'desc' (optional, default: 'desc')
    """
    try:
        base_currency = (
            request.args.get("base", "").upper() if request.args.get("base") else None
        )
        target_currency = (
            request.args.get("target", "").upper()
            if request.args.get("target")
            else None
        )
        from_date_str = request.args.get("from_date")
        to_date_str = request.args.get("to_date")
        limit = min(int(request.args.get("limit", 100)), 1000)  # Max 1000 records
        order = request.args.get("order", "desc").lower()

        # Validate order parameter
        if order not in ["asc", "desc"]:
            return jsonify({"error": "Order must be 'asc' or 'desc'"}), 400

        # Parse dates
        try:
            if from_date_str:
                from_date = datetime.strptime(from_date_str, "%Y-%m-%d")
            else:
                from_date = datetime.now() - timedelta(days=7)  # Default: 7 days ago

            if to_date_str:
                to_date = datetime.strptime(to_date_str, "%Y-%m-%d")
                # Add 23:59:59 to include the entire day
                to_date = to_date.replace(hour=23, minute=59, second=59)
            else:
                to_date = datetime.now()  # Default: now

        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        # Validate date range
        if from_date > to_date:
            return jsonify({"error": "from_date cannot be later than to_date"}), 400

        # Build query
        query = (
            db.session.query(AggregatedRate, CurrencyPair)
            .join(CurrencyPair, AggregatedRate.currency_pair_id == CurrencyPair.id)
            .filter(AggregatedRate.aggregated_at >= from_date)
            .filter(AggregatedRate.aggregated_at <= to_date)
        )

        # Apply currency filters if provided
        if base_currency:
            # Validate base currency
            error = CurrencyPair.validate_currency(base_currency)
            if error:
                return jsonify({"error": f"Invalid base currency: {error}"}), 400
            query = query.filter(CurrencyPair.base_currency == base_currency)

        if target_currency:
            # Validate target currency
            error = CurrencyPair.validate_currency(target_currency)
            if error:
                return jsonify({"error": f"Invalid target currency: {error}"}), 400
            query = query.filter(CurrencyPair.target_currency == target_currency)

        # Apply ordering
        if order == "desc":
            query = query.order_by(AggregatedRate.aggregated_at.desc())
        else:
            query = query.order_by(AggregatedRate.aggregated_at.asc())

        # Apply limit
        results = query.limit(limit).all()

        # Serialize results
        historical_rates = []
        for agg_rate, currency_pair in results:
            rate_dict = agg_rate.to_dict()
            rate_dict["base_currency"] = currency_pair.base_currency
            rate_dict["target_currency"] = currency_pair.target_currency
            historical_rates.append(rate_dict)

        logger.info(f"Fetched {len(historical_rates)} historical rates")
        return jsonify(
            {
                "historical_rates": historical_rates,
                "count": len(historical_rates),
                "filters": {
                    "base_currency": base_currency,
                    "target_currency": target_currency,
                    "from_date": from_date.strftime("%Y-%m-%d"),
                    "to_date": to_date.strftime("%Y-%m-%d"),
                    "limit": limit,
                    "order": order,
                },
            }
        )

    except Exception as e:
        logger.error(f"Error fetching historical rates: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

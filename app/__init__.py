# Flask app initialization
import os

from flask import Flask
from loguru import logger

from config import Config

from .extensions import db


def create_app():
    app = Flask(__name__)

    logger.info(f"MY IP: {os.environ.get('DB_HOST')}")

    app.config.from_object(Config)

    db.init_app(app)

    # Initialize OpenTelemetry (only if enabled)
    if app.config.get("TELEMETRY_ENABLED", True):
        try:
            from .telemetry import setup_telemetry, create_custom_metrics

            # Setup telemetry with Flask app and DB engine
            tracer, meter = setup_telemetry(app=app, db_engine=db.engine)

            # Create and store custom metrics
            if meter:
                app.custom_metrics = create_custom_metrics(meter)
                logger.info("Custom metrics initialized")

            # Store tracer and meter on app for access in routes
            app.tracer = tracer
            app.meter = meter
            logger.info("Telemetry initialization complete")
        except Exception as e:
            logger.error(f"Failed to initialize telemetry: {e}")
            # Continue without telemetry
            app.tracer = None
            app.meter = None
            app.custom_metrics = {}

    # register models
    # blueprints
    from flask import Blueprint

    from app import models

    from .api.admin import admin_bp
    from .api.auth import auth_bp
    from .api.rates import rates_bp

    api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1.0")

    api_v1.register_blueprint(auth_bp)
    api_v1.register_blueprint(rates_bp)
    api_v1.register_blueprint(admin_bp)

    app.register_blueprint(api_v1)
    return app

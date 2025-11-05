# Flask app initialization
import os

from flask import Flask

from config import Config

from .extensions import db


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    # Initialize structured logging FIRST (before any other logging occurs)
    from .utils.logging import setup_logging

    # Determine log format based on environment
    # Use JSON logs in production, human-readable in development
    json_logs = os.getenv("FLASK_ENV", "development") == "production"
    log_level = os.getenv("LOG_LEVEL", "INFO")

    setup_logging(app, log_level=log_level, json_logs=json_logs)

    # Now we can use the logger
    from loguru import logger

    logger.info(
        "Application starting",
        db_host=os.environ.get("DB_HOST"),
        environment=os.getenv("FLASK_ENV", "development"),
        log_level=log_level,
        json_logs=json_logs,
    )

    db.init_app(app)

    # Initialize OpenTelemetry (only if enabled)
    if app.config.get("TELEMETRY_ENABLED", False):
        try:
            from .telemetry import create_custom_metrics, setup_telemetry

            # Setup telemetry with Flask app first (without db_engine)
            # DB engine will be instrumented after app context is available
            with app.app_context():
                tracer, meter = setup_telemetry(app=app, db_engine=db.engine)

            # Create and store custom metrics
            if meter:
                app.custom_metrics = create_custom_metrics(meter)
                logger.info(
                    "Custom metrics initialized", metric_count=len(app.custom_metrics)
                )

            # Store tracer and meter on app for access in routes
            app.tracer = tracer
            app.meter = meter
            logger.info(
                "Telemetry initialization complete",
                tracing_enabled=tracer is not None,
                metrics_enabled=meter is not None,
            )
        except Exception as e:
            logger.error(
                "Failed to initialize telemetry",
                error=str(e),
                error_type=type(e).__name__,
            )
            # Continue without telemetry
            app.tracer = None
            app.meter = None
            app.custom_metrics = {}

    # Initialize logging middleware
    from .middleware.logging_middleware import setup_logging_middleware

    setup_logging_middleware(app)
    logger.info("Logging middleware initialized")

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

    # Health check endpoint (no authentication required)
    @app.route("/health", methods=["GET"])
    def health_check():
        """Health check endpoint for ECS and load balancer"""
        from flask import jsonify

        health_status = {
            "status": "healthy",
            "service": "forex-aggregator",
            "environment": os.getenv("FLASK_ENV", "unknown"),
        }

        # Check database connection
        try:
            with app.app_context():
                db.session.execute(db.text("SELECT 1"))
            health_status["database"] = "connected"
        except Exception as e:
            health_status["database"] = f"error: {str(e)}"
            health_status["status"] = "unhealthy"
            return jsonify(health_status), 503

        return jsonify(health_status), 200

    # Root endpoint
    @app.route("/", methods=["GET"])
    def root():
        """Root endpoint"""
        from flask import jsonify

        return jsonify(
            {
                "service": "WireRemit Forex Aggregator API",
                "version": "1.0",
                "status": "running",
            }
        ), 200

    return app

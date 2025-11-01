# load environment variables from env file
import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # Flask
    DEBUG = os.environ.get("DEBUG")
    SECRET_KEY = os.environ.get("SECRET_KEY")
    CSRF_ENABLED = os.environ.get("CSRF_ENABLED")
    UUID_GENERATOR_FIELD_NAME = os.environ.get("UUID_GENERATOR_FIELD_NAME")

    # Database
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Exchange Rate API Clients
    EXCHANGE_RATE_API_KEY = os.environ.get("EXCHANGE_RATE_API_KEY")
    FIXER_API_KEY = os.environ.get("FIXER_API_KEY")
    POLYGON_API_KEY = os.environ.get("POLYGON_API_KEY")
    CURRENCY_LAYER_API_KEY = os.environ.get("CURRENCY_LAYER_API_KEY")

    # CELERY CONFIGS
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND")

    # JWT Config
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS"))

    # Telemetry/Observability Configuration
    TELEMETRY_ENABLED = os.getenv("TELEMETRY_ENABLED", "true").lower() == "true"
    OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "forex-aggregator")
    OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"
    )
    OTEL_ENABLE_TRACING = os.getenv("OTEL_ENABLE_TRACING", "true").lower() == "true"
    OTEL_ENABLE_METRICS = os.getenv("OTEL_ENABLE_METRICS", "true").lower() == "true"
    OTEL_ENABLE_PROMETHEUS = (
        os.getenv("OTEL_ENABLE_PROMETHEUS", "true").lower() == "true"
    )
    PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "8000"))
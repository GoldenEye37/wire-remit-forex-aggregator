"""
OpenTelemetry configuration for application observability.

This module sets up:
- Distributed tracing with Jaeger
- Metrics collection with Prometheus
- Automatic instrumentation for Flask, SQLAlchemy, Redis, and HTTP requests
"""

import logging
import os

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import start_http_server

logger = logging.getLogger(__name__)


class TelemetryConfig:
    """Centralized telemetry configuration."""

    def __init__(self):
        # Service information
        self.service_name = os.getenv("OTEL_SERVICE_NAME", "forex-aggregator")
        self.service_version = os.getenv("VERSION", "1.0.0")
        self.environment = os.getenv("FLASK_ENV", "development")

        # OpenTelemetry Collector endpoint
        self.otlp_endpoint = os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"
        )

        # Prometheus metrics
        self.prometheus_port = int(os.getenv("PROMETHEUS_PORT", "8000"))

        # Feature flags
        self.enable_tracing = os.getenv("OTEL_ENABLE_TRACING", "true").lower() == "true"
        self.enable_metrics = os.getenv("OTEL_ENABLE_METRICS", "true").lower() == "true"
        self.enable_prometheus = (
            os.getenv("OTEL_ENABLE_PROMETHEUS", "true").lower() == "true"
        )

        # Additional resource attributes
        self.resource_attributes = self._parse_resource_attributes()

    def _parse_resource_attributes(self) -> dict:
        """Parse additional resource attributes from environment."""
        attrs = {
            "service.name": self.service_name,
            "service.version": self.service_version,
            "deployment.environment": self.environment,
        }

        # Parse OTEL_RESOURCE_ATTRIBUTES if set
        resource_attrs_str = os.getenv("OTEL_RESOURCE_ATTRIBUTES", "")
        if resource_attrs_str:
            for attr in resource_attrs_str.split(","):
                if "=" in attr:
                    key, value = attr.split("=", 1)
                    attrs[key.strip()] = value.strip()

        return attrs


def setup_telemetry(
    app=None, db_engine=None
) -> tuple[trace.Tracer | None, metrics.Meter | None]:
    """
    Initialize OpenTelemetry instrumentation with traces and metrics.

    Args:
        app: Flask application instance
        db_engine: SQLAlchemy engine instance

    Returns:
        Tuple of (tracer, meter) for custom instrumentation
    """
    config = TelemetryConfig()

    # Create resource with service information
    resource = Resource.create(config.resource_attributes)

    tracer = None
    meter = None

    # Setup Tracing
    if config.enable_tracing:
        tracer = _setup_tracing(resource, config)
        logger.info(
            f"Tracing enabled for service '{config.service_name}' "
            f"sending to {config.otlp_endpoint}"
        )

    # Setup Metrics
    if config.enable_metrics:
        meter = _setup_metrics(resource, config)
        logger.info(
            f"Metrics enabled for service '{config.service_name}' "
            f"sending to {config.otlp_endpoint}"
        )

    # Instrument libraries
    _instrument_libraries(app, db_engine)

    return tracer, meter


def _setup_tracing(resource: Resource, config: TelemetryConfig) -> trace.Tracer:
    """Configure distributed tracing."""
    # Create OTLP trace exporter
    otlp_exporter = OTLPSpanExporter(endpoint=config.otlp_endpoint, insecure=True)

    # Create tracer provider
    tracer_provider = TracerProvider(resource=resource)

    # Add batch span processor
    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Set global tracer provider
    trace.set_tracer_provider(tracer_provider)

    # Return a tracer instance
    return trace.get_tracer(__name__)


def _setup_metrics(resource: Resource, config: TelemetryConfig) -> metrics.Meter:
    """Configure metrics collection."""
    metric_readers = []

    # OTLP Metrics Exporter
    otlp_metric_exporter = OTLPMetricExporter(
        endpoint=config.otlp_endpoint, insecure=True
    )
    metric_readers.append(
        PeriodicExportingMetricReader(otlp_metric_exporter, export_interval_millis=5000)
    )

    # Prometheus Exporter (optional)
    # NOTE: Disabled when using Gunicorn with multiple workers as each worker
    # would try to bind to the same port. Use OTLP exporter instead.
    if config.enable_prometheus:
        import os

        # Only start Prometheus server in the main process or if running with single worker
        worker_id = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
        if worker_id is None:  # Not using multiprocess mode
            try:
                prometheus_reader = PrometheusMetricReader()
                metric_readers.append(prometheus_reader)

                # Start Prometheus metrics HTTP server
                start_http_server(port=config.prometheus_port, addr="0.0.0.0")
                logger.info(
                    f"Prometheus metrics server started on port {config.prometheus_port}"
                )
            except OSError as e:
                logger.warning(f"Could not start Prometheus metrics server: {e}")
        else:
            logger.info("Skipping Prometheus HTTP server in multiprocess mode")

    # Create meter provider
    meter_provider = MeterProvider(resource=resource, metric_readers=metric_readers)

    # Set global meter provider
    metrics.set_meter_provider(meter_provider)

    # Return a meter instance
    return metrics.get_meter(__name__)


def _instrument_libraries(app=None, db_engine=None):
    """Automatically instrument common libraries."""
    # Instrument Flask
    if app:
        FlaskInstrumentor().instrument_app(app)
        logger.info("Flask instrumentation enabled")

    # Instrument SQLAlchemy
    if db_engine:
        SQLAlchemyInstrumentor().instrument(engine=db_engine)
        logger.info("SQLAlchemy instrumentation enabled")

    # Instrument Redis
    try:
        RedisInstrumentor().instrument()
        logger.info("Redis instrumentation enabled")
    except Exception as e:
        logger.warning(f"Could not instrument Redis: {e}")

    # Instrument HTTP requests library
    RequestsInstrumentor().instrument()
    logger.info("Requests instrumentation enabled")


def create_custom_metrics(meter: metrics.Meter) -> dict:
    """
    Create custom application-specific metrics.

    Args:
        meter: OpenTelemetry meter instance

    Returns:
        Dictionary of metric instruments
    """
    return {
        # Counter for total API requests
        "api_requests_total": meter.create_counter(
            name="api.requests.total",
            description="Total number of API requests",
            unit="1",
        ),
        # Histogram for request duration
        "request_duration": meter.create_histogram(
            name="api.request.duration",
            description="API request duration in milliseconds",
            unit="ms",
        ),
        # Counter for forex rate fetches
        "rate_fetches_total": meter.create_counter(
            name="forex.rate_fetches.total",
            description="Total number of forex rate fetch attempts",
            unit="1",
        ),
        # Counter for provider errors
        "provider_errors_total": meter.create_counter(
            name="forex.provider_errors.total",
            description="Total number of provider errors",
            unit="1",
        ),
        # Gauge for active connections
        "active_connections": meter.create_up_down_counter(
            name="app.active_connections",
            description="Number of active connections",
            unit="1",
        ),
        # Counter for cache hits/misses
        "cache_operations": meter.create_counter(
            name="cache.operations.total",
            description="Total cache operations (hits/misses)",
            unit="1",
        ),
    }


def get_tracer() -> trace.Tracer:
    """Get the application tracer for manual instrumentation."""
    return trace.get_tracer(__name__)


def get_meter() -> metrics.Meter:
    """Get the application meter for manual instrumentation."""
    return metrics.get_meter(__name__)

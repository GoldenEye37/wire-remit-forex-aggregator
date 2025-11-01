# Telemetry and Observability Configuration

This document describes the comprehensive telemetry and observability setup for the Forex Aggregator application.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Quick Start](#quick-start)
5. [Configuration](#configuration)
6. [Accessing the Telemetry Stack](#accessing-the-telemetry-stack)
7. [Custom Instrumentation](#custom-instrumentation)
8. [Metrics Reference](#metrics-reference)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

---

## Overview

The Forex Aggregator application uses **OpenTelemetry (OTEL)** for observability, providing:

- **Distributed Tracing**: Track requests across services using Jaeger
- **Metrics Collection**: Monitor application performance with Prometheus
- **Visualization**: Create dashboards and alerts using Grafana
- **Automatic Instrumentation**: Zero-code instrumentation for Flask, SQLAlchemy, Redis, and HTTP requests

### Key Benefits

- Full visibility into application performance
- Easy debugging of distributed systems
- Proactive monitoring and alerting
- Performance optimization insights
- Compliance and audit trails

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Forex Aggregator App                      │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  OpenTelemetry SDK (auto-instrumentation)              │  │
│  │  - Flask, SQLAlchemy, Redis, Requests                  │  │
│  └────────────────────────────────────────────────────────┘  │
│                           │                                   │
│                           │ OTLP (gRPC/HTTP)                 │
│                           ▼                                   │
└───────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│               OpenTelemetry Collector                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  Receivers   │→ │  Processors  │→ │  Exporters   │        │
│  │  (OTLP)      │  │  (Batch)     │  │  (Multiple)  │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└────────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
┌─────────────────────────┐  ┌─────────────────────────┐
│   Jaeger (Traces)       │  │  Prometheus (Metrics)   │
│   Port: 16686           │  │  Port: 9090             │
└─────────────────────────┘  └─────────────────────────┘
                │                       │
                └───────────┬───────────┘
                            │
                            ▼
                ┌─────────────────────────┐
                │   Grafana (Dashboards)  │
                │   Port: 3000            │
                └─────────────────────────┘
```

---

## Components

### 1. OpenTelemetry SDK

The application uses OpenTelemetry instrumentation libraries:

- `opentelemetry-api`: Core API for traces and metrics
- `opentelemetry-sdk`: SDK implementation
- `opentelemetry-instrumentation-flask`: Auto-instrumentation for Flask
- `opentelemetry-instrumentation-sqlalchemy`: Database query tracking
- `opentelemetry-instrumentation-redis`: Cache operation tracking
- `opentelemetry-instrumentation-requests`: External HTTP request tracking

### 2. OpenTelemetry Collector

The collector receives, processes, and exports telemetry data:

- **Receivers**: OTLP (gRPC on 4317, HTTP on 4318)
- **Processors**: Batching, resource attributes, memory limits
- **Exporters**: Jaeger, Prometheus, logging, file

Configuration file: [otel-collector-config.yaml](../otel-collector-config.yaml)

### 3. Jaeger

Distributed tracing backend:

- **UI Port**: 16686
- **OTLP Port**: 4317
- Visualizes request traces across services
- Identifies performance bottlenecks

### 4. Prometheus

Time-series metrics database:

- **UI Port**: 9090
- **Metrics Port**: 8888 (OTEL Collector)
- **Metrics Port**: 8889 (OTEL Prometheus Exporter)
- Scrapes and stores application metrics

Configuration file: [prometheus.yml](../prometheus.yml)

### 5. Grafana

Visualization and dashboarding:

- **UI Port**: 3000
- **Default Credentials**: admin/admin
- Pre-configured datasources (Prometheus, Jaeger)
- Custom dashboards for Forex Aggregator

Configuration files:
- [grafana/datasources/datasources.yml](../grafana/datasources/datasources.yml)
- [grafana/dashboards/forex-aggregator-overview.json](../grafana/dashboards/forex-aggregator-overview.json)

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Full Stack

```bash
docker-compose up -d
```

This will start:
- Forex Aggregator application
- Redis
- PostgreSQL
- OpenTelemetry Collector
- Jaeger
- Prometheus
- Grafana

### 3. Verify Services

Check that all services are running:

```bash
docker-compose ps
```

Expected output:
```
wiremit-forex-aggregator   Up      0.0.0.0:5000->5000/tcp
wiremit-redis              Up      0.0.0.0:6379->6379/tcp
wiremit-postgres           Up      0.0.0.0:5432->5432/tcp
wiremit-otel-collector     Up      Multiple ports
wiremit-jaeger             Up      0.0.0.0:16686->16686/tcp
wiremit-prometheus         Up      0.0.0.0:9090->9090/tcp
wiremit-grafana            Up      0.0.0.0:3000->3000/tcp
```

### 4. Access the Dashboards

- **Application**: http://localhost:5000
- **Jaeger UI**: http://localhost:16686
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000

---

## Configuration

### Environment Variables

Configure telemetry using these environment variables (set in `.env` or `docker-compose.yml`):

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEMETRY_ENABLED` | `true` | Enable/disable telemetry |
| `OTEL_SERVICE_NAME` | `forex-aggregator` | Service name in traces |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://otel-collector:4317` | OTLP collector endpoint |
| `OTEL_ENABLE_TRACING` | `true` | Enable distributed tracing |
| `OTEL_ENABLE_METRICS` | `true` | Enable metrics collection |
| `OTEL_ENABLE_PROMETHEUS` | `true` | Enable Prometheus exporter |
| `PROMETHEUS_PORT` | `8000` | Port for Prometheus metrics |
| `OTEL_RESOURCE_ATTRIBUTES` | `service.version=latest` | Additional resource attributes |

### Example .env File

```env
# Telemetry Configuration
TELEMETRY_ENABLED=true
OTEL_SERVICE_NAME=forex-aggregator
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_ENABLE_TRACING=true
OTEL_ENABLE_METRICS=true
OTEL_ENABLE_PROMETHEUS=true
PROMETHEUS_PORT=8000
OTEL_RESOURCE_ATTRIBUTES=service.version=1.0.0,deployment.environment=production
VERSION=1.0.0
```

### Disabling Telemetry

To run without telemetry:

```env
TELEMETRY_ENABLED=false
```

Or in code:

```python
# In config.py
TELEMETRY_ENABLED = False
```

---

## Accessing the Telemetry Stack

### Jaeger - Distributed Tracing

1. Open http://localhost:16686
2. Select "forex-aggregator" from the Service dropdown
3. Click "Find Traces" to see all traces
4. Click on a trace to see detailed span information

**Use Cases**:
- Debugging slow API requests
- Understanding request flow
- Identifying bottlenecks
- Analyzing external API calls

### Prometheus - Metrics

1. Open http://localhost:9090
2. Click "Graph" to query metrics
3. Example queries:
   ```promql
   # Request rate
   rate(api_requests_total[5m])

   # P95 latency
   histogram_quantile(0.95, rate(api_request_duration_bucket[5m]))

   # Error rate
   rate(forex_provider_errors_total[5m])
   ```

### Grafana - Dashboards

1. Open http://localhost:3000
2. Login with `admin/admin`
3. Navigate to "Dashboards" → "Forex Aggregator - Overview"

**Pre-built Panels**:
- API Request Rate
- Response Time (P95)
- Forex Rate Fetch Rate by Provider
- Provider Errors
- Cache Hit Rate
- Active Connections

---

## Custom Instrumentation

### Using the Tracer

Add custom spans to track specific operations:

```python
from flask import current_app

def my_function():
    # Get the tracer
    tracer = current_app.tracer

    if tracer:
        # Create a custom span
        with tracer.start_as_current_span("my_operation") as span:
            # Add attributes
            span.set_attribute("user_id", "12345")
            span.set_attribute("operation_type", "fetch_rate")

            # Your code here
            result = expensive_operation()

            # Add events
            span.add_event("Operation completed", {
                "result_count": len(result)
            })

            return result
```

### Using Custom Metrics

Track custom metrics:

```python
from flask import current_app

def process_rate_fetch(provider, success):
    metrics = current_app.custom_metrics

    if metrics:
        # Increment rate fetch counter
        metrics['rate_fetches_total'].add(1, {
            "provider": provider,
            "status": "success" if success else "failure"
        })

        # Track errors
        if not success:
            metrics['provider_errors_total'].add(1, {
                "provider": provider,
                "error_type": "timeout"
            })
```

### Recording Request Duration

```python
import time
from flask import current_app

def timed_operation():
    metrics = current_app.custom_metrics

    if metrics:
        start_time = time.time()

        # Your operation
        result = do_work()

        # Record duration
        duration_ms = (time.time() - start_time) * 1000
        metrics['request_duration'].record(duration_ms, {
            "operation": "do_work"
        })

        return result
```

### Cache Operations

```python
def get_from_cache(key):
    metrics = current_app.custom_metrics

    value = redis_client.get(key)

    if metrics:
        operation = "hit" if value else "miss"
        metrics['cache_operations'].add(1, {
            "operation": operation,
            "cache_type": "redis"
        })

    return value
```

---

## Metrics Reference

### Automatic Metrics

These metrics are automatically collected:

| Metric | Type | Description |
|--------|------|-------------|
| `http_server_duration` | Histogram | HTTP request duration |
| `http_server_active_requests` | Counter | Active HTTP requests |
| `db_client_duration` | Histogram | Database query duration |
| `redis_duration` | Histogram | Redis operation duration |

### Custom Application Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `api.requests.total` | Counter | method, endpoint, status | Total API requests |
| `api.request.duration` | Histogram | endpoint | Request duration in ms |
| `forex.rate_fetches.total` | Counter | provider, status | Rate fetch attempts |
| `forex.provider_errors.total` | Counter | provider, error_type | Provider errors |
| `app.active_connections` | UpDownCounter | - | Active connections |
| `cache.operations.total` | Counter | operation, cache_type | Cache hits/misses |

---

## Troubleshooting

### Telemetry Not Working

1. **Check environment variables**:
   ```bash
   docker-compose exec forex-aggregator env | grep OTEL
   ```

2. **Verify OTEL Collector is running**:
   ```bash
   docker-compose logs otel-collector
   ```

3. **Check application logs**:
   ```bash
   docker-compose logs forex-aggregator | grep -i telemetry
   ```

### No Traces in Jaeger

1. Ensure `OTEL_ENABLE_TRACING=true`
2. Check OTLP endpoint is correct: `http://otel-collector:4317`
3. Verify Jaeger is receiving data:
   ```bash
   docker-compose logs jaeger
   ```

### No Metrics in Prometheus

1. Ensure `OTEL_ENABLE_METRICS=true`
2. Check Prometheus targets: http://localhost:9090/targets
3. Verify OTEL Collector metrics endpoint:
   ```bash
   curl http://localhost:8889/metrics
   ```

### Grafana Dashboards Empty

1. Verify datasources are configured: http://localhost:3000/datasources
2. Check Prometheus connection: http://localhost:3000/connections/datasources/prometheus
3. Ensure metrics are being collected in Prometheus first

### High Memory Usage

If OTEL Collector uses too much memory:

1. Adjust memory limits in [otel-collector-config.yaml](../otel-collector-config.yaml):
   ```yaml
   processors:
     memory_limiter:
       check_interval: 1s
       limit_mib: 256  # Reduce from 512
   ```

2. Increase batch timeout:
   ```yaml
   processors:
     batch:
       timeout: 30s  # Increase from 10s
   ```

---

## Best Practices

### 1. Naming Conventions

- **Service Names**: Use lowercase with hyphens (e.g., `forex-aggregator`)
- **Span Names**: Use verb-noun format (e.g., `fetch_rate`, `process_payment`)
- **Metric Names**: Use dots for hierarchy (e.g., `api.requests.total`)
- **Attributes**: Use underscores (e.g., `user_id`, `provider_name`)

### 2. Sampling

For production, use sampling to reduce overhead:

```python
# In telemetry.py
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

# Sample 10% of traces
sampler = TraceIdRatioBased(0.1)
tracer_provider = TracerProvider(resource=resource, sampler=sampler)
```

### 3. Sensitive Data

Never log sensitive information in spans or metrics:

```python
# Bad
span.set_attribute("credit_card", card_number)
span.set_attribute("password", user_password)

# Good
span.set_attribute("user_id_hash", hash(user_id))
span.set_attribute("payment_method_type", "credit_card")
```

### 4. Cardinality

Avoid high-cardinality labels in metrics:

```python
# Bad - user_id has high cardinality
metrics['requests'].add(1, {"user_id": user_id})

# Good - use categorical labels
metrics['requests'].add(1, {"user_type": "premium"})
```

### 5. Error Handling

Always handle telemetry errors gracefully:

```python
def my_function():
    try:
        tracer = current_app.tracer
        if tracer:
            with tracer.start_as_current_span("operation"):
                # Your code
                pass
    except Exception as e:
        # Log but don't fail the operation
        logger.warning(f"Telemetry error: {e}")
        # Continue with business logic
```

### 6. Performance

- Use batch processors to reduce network calls
- Set appropriate export intervals (5-10 seconds)
- Monitor OTEL Collector resource usage
- Use sampling in high-traffic environments

### 7. Alerts

Create alerts for critical metrics in Prometheus:

```yaml
# Example alert rules
groups:
  - name: forex_aggregator
    rules:
      - alert: HighErrorRate
        expr: rate(forex_provider_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High provider error rate"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(api_request_duration_bucket[5m])) > 1000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API latency above 1s"
```

---

## Production Considerations

### Security

1. **Use TLS** for OTLP endpoints in production
2. **Secure Grafana** with proper authentication
3. **Restrict network access** to telemetry ports
4. **Rotate credentials** regularly

### Scalability

1. **Use OTLP HTTP/2** for better performance
2. **Deploy OTEL Collector as sidecar** or daemonset
3. **Use external storage** for Prometheus (e.g., Thanos)
4. **Implement sampling** to reduce data volume

### Reliability

1. **Monitor the monitors** - set up alerts for telemetry stack health
2. **Use persistent storage** for Prometheus and Grafana
3. **Implement backup strategies** for dashboards and config
4. **Test failover scenarios**

---

## Additional Resources

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [OTEL Python Instrumentation](https://opentelemetry-python.readthedocs.io/)

---

## Support

For issues or questions:

1. Check application logs: `docker-compose logs forex-aggregator`
2. Check OTEL Collector logs: `docker-compose logs otel-collector`
3. Review this documentation
4. Contact the development team

---

**Last Updated**: 2025-11-01
**Version**: 1.0.0

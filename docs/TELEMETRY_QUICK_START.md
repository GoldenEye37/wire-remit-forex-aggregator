# Telemetry Quick Start Guide

Get up and running with application telemetry in 5 minutes.

## Prerequisites

- Docker and Docker Compose installed
- Forex Aggregator application cloned

## Setup Steps

### 1. Environment Configuration (Optional)

The application comes with telemetry enabled by default. To customize:

```bash
# Copy the example telemetry config
cp .env.telemetry.example .env

# Edit the values as needed
nano .env
```

### 2. Start the Stack

```bash
# Start all services including telemetry stack
docker-compose up -d

# Verify all services are running
docker-compose ps
```

Expected services:
- ✅ forex-aggregator (Application)
- ✅ redis (Cache)
- ✅ postgres (Database)
- ✅ otel-collector (Telemetry collector)
- ✅ jaeger (Tracing)
- ✅ prometheus (Metrics)
- ✅ grafana (Dashboards)

### 3. Generate Some Traffic

```bash
# Make some API requests to generate telemetry data
curl http://localhost:5000/api/v1.0/rates

# Or use your API client to interact with the application
```

### 4. View Telemetry Data

#### Traces in Jaeger
1. Open http://localhost:16686
2. Select "forex-aggregator" from Service dropdown
3. Click "Find Traces"
4. Click on any trace to see details

#### Metrics in Prometheus
1. Open http://localhost:9090
2. Click "Graph"
3. Try these queries:
   ```
   rate(api_requests_total[5m])
   histogram_quantile(0.95, rate(api_request_duration_bucket[5m]))
   ```

#### Dashboards in Grafana
1. Open http://localhost:3000
2. Login: `admin` / `admin`
3. Go to Dashboards → Forex Aggregator - Overview

## Access URLs

| Service | URL | Default Credentials |
|---------|-----|---------------------|
| Application | http://localhost:5000 | - |
| Jaeger UI | http://localhost:16686 | - |
| Prometheus | http://localhost:9090 | - |
| Grafana | http://localhost:3000 | admin/admin |

## Common Tasks

### View Application Logs

```bash
docker-compose logs -f forex-aggregator
```

Look for lines like:
```
Tracing enabled for service 'forex-aggregator'
Metrics enabled for service 'forex-aggregator'
Telemetry initialization complete
```

### Check OTEL Collector Status

```bash
# View collector logs
docker-compose logs otel-collector

# Check health endpoint
curl http://localhost:13133
```

### Disable Telemetry

Set in `.env`:
```env
TELEMETRY_ENABLED=false
```

Then restart:
```bash
docker-compose restart forex-aggregator
```

### View Custom Metrics

In Prometheus, query for application-specific metrics:

```promql
# Forex rate fetches by provider
rate(forex_rate_fetches_total[5m])

# Provider errors
rate(forex_provider_errors_total[5m])

# Cache hit rate
rate(cache_operations_total{operation="hit"}[5m]) / rate(cache_operations_total[5m]) * 100
```

## Troubleshooting

### No traces appearing in Jaeger?

1. Check OTEL Collector is running:
   ```bash
   docker-compose ps otel-collector
   ```

2. Verify endpoint configuration:
   ```bash
   docker-compose exec forex-aggregator env | grep OTEL_EXPORTER
   ```

3. Check collector logs for errors:
   ```bash
   docker-compose logs otel-collector | grep -i error
   ```

### Grafana shows "No Data"?

1. Verify Prometheus is scraping metrics:
   - Open http://localhost:9090/targets
   - All targets should show "UP"

2. Check datasource connection:
   - Go to http://localhost:3000/connections/datasources
   - Test the Prometheus datasource

3. Wait a few minutes for data to accumulate

### High resource usage?

1. Reduce metrics collection frequency in `prometheus.yml`:
   ```yaml
   scrape_interval: 30s  # Increase from 15s
   ```

2. Adjust OTEL Collector batch size in `otel-collector-config.yaml`:
   ```yaml
   processors:
     batch:
       timeout: 30s  # Increase from 10s
   ```

## Next Steps

- 📖 Read the [full telemetry documentation](TELEMETRY.md)
- 🎨 Create custom dashboards in Grafana
- 🚨 Set up alerts in Prometheus
- 📊 Add custom metrics to your code
- 🔍 Use traces to debug performance issues

## Need Help?

- Check logs: `docker-compose logs [service-name]`
- Review documentation: [TELEMETRY.md](TELEMETRY.md)
- Restart services: `docker-compose restart`
- Full reset: `docker-compose down && docker-compose up -d`

---

**Tip**: Keep Grafana, Jaeger, and Prometheus open in separate browser tabs for easy monitoring!

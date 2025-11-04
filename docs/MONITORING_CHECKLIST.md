# Comprehensive Monitoring Checklist & Implementation Plan
## WireRemit Forex Aggregator

**Version:** 1.0
**Last Updated:** 2025-11-03
**Status:** Implementation in Progress

---

## 📊 Current State Assessment

### ✅ Already Implemented
- [x] OpenTelemetry SDK integrated
- [x] Automatic instrumentation (Flask, SQLAlchemy, Redis, HTTP requests)
- [x] Custom metrics defined (but not used)
- [x] OTEL Collector configured
- [x] Prometheus scraping configured
- [x] Jaeger for distributed tracing
- [x] Grafana for visualization
- [x] CloudWatch Logs integration
- [x] ECS Container Insights enabled

### ❌ Missing/Incomplete
- [ ] Custom metrics recording in code
- [ ] Custom spans for business logic
- [ ] Structured logging
- [ ] Business event tracking
- [ ] Celery task monitoring
- [ ] Database connection pool monitoring
- [ ] Redis connection monitoring
- [ ] Queue depth metrics
- [ ] Alert rules configured
- [ ] Grafana dashboards created

---

## 🎯 Comprehensive Monitoring Checklist

## 1. Application Layer

### 1.1 Metrics (OpenTelemetry)

#### HTTP Metrics
- [ ] **RPS (Requests Per Second)**
  - [ ] Total requests counter
  - [ ] Requests by endpoint
  - [ ] Requests by method (GET, POST, etc.)
  - [ ] Requests by status code (2xx, 4xx, 5xx)
  - **Implementation:** `app.custom_metrics['api_requests_total']`
  - **Files:** `app/api/*.py`, `app/decorators.py`

- [ ] **Latency**
  - [ ] Request duration histogram (p50, p95, p99)
  - [ ] Latency by endpoint
  - [ ] Slow request threshold alerts (>1s, >5s)
  - **Implementation:** `app.custom_metrics['request_duration']`
  - **Files:** `app/api/*.py`

- [ ] **Error Rate**
  - [ ] Total error count
  - [ ] Error rate percentage
  - [ ] Errors by type (4xx vs 5xx)
  - [ ] Errors by endpoint
  - **Implementation:** Counter for failed requests
  - **Files:** `app/api/*.py`

- [ ] **Active Sessions**
  - [ ] Current authenticated users
  - [ ] JWT tokens issued
  - [ ] Session duration tracking
  - **Implementation:** `app.custom_metrics['active_connections']`
  - **Files:** `app/decorators.py`, `app/api/auth.py`

#### Business Metrics
- [ ] **Rate Fetching**
  - [ ] Total rate fetch attempts
  - [ ] Successful rate fetches by provider
  - [ ] Failed rate fetches by provider
  - [ ] Rate fetch duration by provider
  - **Implementation:** `app.custom_metrics['rate_fetches_total']`
  - **Files:** `app/services/rate_fetcher.py`

- [ ] **Provider Health**
  - [ ] Provider availability percentage
  - [ ] Provider error count by type
  - [ ] Provider response time
  - [ ] Provider retry count
  - **Implementation:** `app.custom_metrics['provider_errors_total']`
  - **Files:** `app/services/rate_fetcher.py`, `app/services/providers/*.py`

- [ ] **Rate Aggregation**
  - [ ] Rates aggregated count
  - [ ] Aggregation duration
  - [ ] Currency pairs processed
  - [ ] Stale rates detected
  - **Implementation:** New custom metric needed
  - **Files:** `app/services/rate_processor.py`

- [ ] **Cache Performance**
  - [ ] Cache hit rate
  - [ ] Cache miss rate
  - [ ] Cache eviction count
  - **Implementation:** `app.custom_metrics['cache_operations']`
  - **Files:** Wherever Redis caching is used

### 1.2 Logs (Structured Logging)

- [ ] **Error Logs**
  - [ ] Exception type and message
  - [ ] Stack traces
  - [ ] Failed request details (method, path, user_id)
  - [ ] Error context (rate provider, currency pair)
  - **Implementation:** Structured JSON logging with loguru
  - **Files:** All application files

- [ ] **Business Event Logs**
  - [ ] Rate updates (timestamp, provider, currency_pair, rate_value)
  - [ ] User authentication (user_id, timestamp, success/failure)
  - [ ] Admin operations (action, user_id, timestamp, target)
  - [ ] API key usage (endpoint, timestamp, status)
  - **Implementation:** Structured event logging
  - **Files:** `app/services/*.py`, `app/api/*.py`

- [ ] **Audit Logs**
  - [ ] User registration
  - [ ] Password changes
  - [ ] Admin actions
  - [ ] Rate configuration changes
  - **Implementation:** Audit trail logging
  - **Files:** `app/api/admin.py`, `app/api/auth.py`

### 1.3 Traces (OpenTelemetry/Tempo)

- [ ] **Request Cycle Tracing**
  - [ ] End-to-end request spans
  - [ ] Database query spans
  - [ ] External API call spans
  - [ ] Redis operation spans
  - **Implementation:** Auto-instrumentation + custom spans
  - **Files:** All request handlers

- [ ] **Custom Spans**
  - [ ] Rate fetching spans (per provider)
  - [ ] Rate aggregation spans
  - [ ] Authentication validation spans
  - [ ] Database transaction spans
  - **Implementation:** Manual span creation with `tracer.start_as_current_span()`
  - **Files:** `app/services/*.py`, `app/decorators.py`

- [ ] **Span Attributes**
  - [ ] user_id
  - [ ] endpoint
  - [ ] http.method, http.status_code
  - [ ] provider_name
  - [ ] currency_pair
  - [ ] error (true/false)
  - [ ] error.type, error.message
  - **Implementation:** `span.set_attribute()`
  - **Files:** All service and API files

---

## 2. Worker Layer (Celery)

### 2.1 Task Metrics

- [ ] **Task Execution**
  - [ ] Tasks received by task name
  - [ ] Tasks started
  - [ ] Tasks succeeded
  - [ ] Tasks failed by error type
  - [ ] Task success rate percentage
  - **Implementation:** Celery signals + OpenTelemetry
  - **Files:** `tasks/*.py`

- [ ] **Task Duration**
  - [ ] Task execution time histogram
  - [ ] Duration by task type
  - [ ] Long-running task detection (>5min)
  - **Implementation:** Celery signals
  - **Files:** `tasks/*.py`

- [ ] **Queue Metrics**
  - [ ] Queue depth by queue name
  - [ ] Messages waiting count
  - [ ] Queue processing rate
  - **Implementation:** Redis queue monitoring
  - **Files:** Custom monitoring script

- [ ] **Dead Letter Queue**
  - [ ] Failed task count
  - [ ] Task retry count
  - [ ] DLQ size
  - [ ] Failed task types
  - **Implementation:** Celery result backend monitoring
  - **Files:** `tasks/celery_app.py`

### 2.2 Worker Health

- [ ] **Worker Status**
  - [ ] Active workers count
  - [ ] Worker pool saturation
  - [ ] Worker restarts
  - **Implementation:** Celery inspect
  - **Files:** Custom monitoring script

### 2.3 Celery Logs

- [ ] **Task Lifecycle Logs**
  - [ ] Task started (task_id, task_name, args, timestamp)
  - [ ] Task completed (task_id, duration, result, timestamp)
  - [ ] Task failed (task_id, error, retry_count, timestamp)
  - [ ] Task retry (task_id, attempt, reason, timestamp)
  - **Implementation:** Celery signals + structured logging
  - **Files:** `tasks/*.py`

---

## 3. Database Layer (PostgreSQL)

### 3.1 Connection Monitoring

- [ ] **Connection Pool**
  - [ ] Active connections count
  - [ ] Idle connections count
  - [ ] Connection pool size
  - [ ] Connection waits
  - [ ] Connection leaks detection
  - **Implementation:** SQLAlchemy pool metrics
  - **Files:** `app/extensions.py`, monitoring script

- [ ] **Connection Health**
  - [ ] Failed connection attempts
  - [ ] Connection errors by type
  - [ ] Connection establishment time
  - **Implementation:** Database health checks
  - **Files:** `app/__init__.py` (health endpoint)

### 3.2 Query Performance

- [ ] **Query Latency**
  - [ ] Slow query log (>1s)
  - [ ] Query duration histogram
  - [ ] Queries by table
  - [ ] Queries by operation (SELECT, INSERT, UPDATE)
  - **Implementation:** SQLAlchemy instrumentation + pg_stat_statements
  - **Files:** Auto-instrumented

- [ ] **Index Efficiency**
  - [ ] Sequential scans count
  - [ ] Index scans count
  - [ ] Missing index suggestions
  - [ ] Index hit rate
  - **Implementation:** PostgreSQL system views
  - **Files:** Custom monitoring queries

- [ ] **Locks and Deadlocks**
  - [ ] Lock wait time
  - [ ] Deadlock count
  - [ ] Blocked queries
  - [ ] Lock holder identification
  - **Implementation:** pg_locks monitoring
  - **Files:** Custom monitoring queries

### 3.3 Database Metrics

- [ ] **Table Statistics**
  - [ ] Table size growth
  - [ ] Row count changes
  - [ ] Vacuum/analyze frequency
  - **Implementation:** pg_stat_user_tables
  - **Files:** Custom monitoring queries

---

## 4. Redis Backend Layer

### 4.1 Connection Monitoring

- [ ] **Connection Pool**
  - [ ] Active Redis connections
  - [ ] Connection errors
  - [ ] Connection timeout rate
  - **Implementation:** Redis instrumentation
  - **Files:** Auto-instrumented via OpenTelemetry

### 4.2 Performance Metrics

- [ ] **Operation Latency**
  - [ ] GET operation latency
  - [ ] SET operation latency
  - [ ] DEL operation latency
  - **Implementation:** Redis instrumentation
  - **Files:** Auto-instrumented

- [ ] **Cache Efficiency**
  - [ ] Hit rate percentage
  - [ ] Miss rate percentage
  - [ ] Eviction count
  - [ ] Memory usage
  - **Implementation:** Redis INFO command
  - **Files:** Custom monitoring script

- [ ] **Queue Operations**
  - [ ] LPUSH/RPUSH rate
  - [ ] LPOP/RPOP rate
  - [ ] List length by key
  - **Implementation:** Redis monitoring
  - **Files:** Custom monitoring script

### 4.3 Health Monitoring

- [ ] **Redis Health**
  - [ ] Availability checks
  - [ ] Memory fragmentation ratio
  - [ ] Keyspace size
  - [ ] Expired keys count
  - **Implementation:** Redis INFO monitoring
  - **Files:** Custom monitoring script

---

## 5. Infrastructure Layer (AWS ECS/Fargate)

### 5.1 Compute Metrics

- [ ] **CPU Utilization**
  - [ ] CPU usage by container
  - [ ] CPU throttling events
  - [ ] CPU limits approached alerts
  - **Implementation:** CloudWatch Container Insights (already enabled)
  - **Source:** ECS Container Insights

- [ ] **Memory**
  - [ ] Memory usage by container
  - [ ] Memory utilization percentage
  - [ ] OOM kill events
  - [ ] Memory limits approached alerts
  - **Implementation:** CloudWatch Container Insights
  - **Source:** ECS Container Insights

### 5.2 Storage and I/O

- [ ] **Disk I/O**
  - [ ] Read/write operations per second
  - [ ] I/O latency
  - [ ] Disk queue length
  - **Implementation:** CloudWatch metrics
  - **Source:** RDS Performance Insights

- [ ] **Storage Usage**
  - [ ] RDS storage used
  - [ ] Storage growth rate
  - [ ] IOPS usage
  - **Implementation:** CloudWatch RDS metrics
  - **Source:** RDS CloudWatch

### 5.3 Network Monitoring

- [ ] **Network Traffic**
  - [ ] Bytes in/out
  - [ ] Packets in/out
  - [ ] Network spikes detection
  - [ ] Traffic patterns by time
  - **Implementation:** CloudWatch network metrics
  - **Source:** ECS/ALB CloudWatch

- [ ] **Load Balancer**
  - [ ] Active connections
  - [ ] Target health status
  - [ ] 5xx error count
  - [ ] Response time
  - **Implementation:** ALB CloudWatch metrics
  - **Source:** ALB CloudWatch

### 5.4 Container Health

- [ ] **Container Lifecycle**
  - [ ] Container starts/stops
  - [ ] Container crash count
  - [ ] Task failure reasons
  - [ ] Deployment success rate
  - **Implementation:** ECS events + CloudWatch
  - **Source:** ECS CloudWatch Events

---

## 🚀 Implementation Plan

### Phase 1: Foundation (Week 1) - CRITICAL

**Goal:** Get core application metrics and traces working

#### 1.1 Implement Custom Metrics Recording
- [ ] Add metrics to all API endpoints (`app/api/*.py`)
  - Record request count, duration, errors
  - Add endpoint and status labels
- [ ] Add metrics to authentication decorator (`app/decorators.py`)
  - Track auth success/failure
  - Track JWT validation time
- [ ] Add metrics to rate fetching (`app/services/rate_fetcher.py`)
  - Track fetch attempts, successes, failures per provider
  - Track fetch duration per provider
- [ ] Add metrics to rate processing (`app/services/rate_processor.py`)
  - Track aggregation count and duration
  - Track currency pairs processed

**Files to Modify:**
- `app/api/rates.py`
- `app/api/auth.py`
- `app/api/admin.py`
- `app/decorators.py`
- `app/services/rate_fetcher.py`
- `app/services/rate_processor.py`

**Acceptance Criteria:**
- Metrics visible in Prometheus
- Metrics scraped successfully every 15s
- No errors in OTEL exporter logs

#### 1.2 Add Custom Tracing
- [ ] Add spans to rate fetching with retry attempts
- [ ] Add spans to rate aggregation
- [ ] Add spans to authentication flow
- [ ] Add error recording to spans
- [ ] Add business attributes to spans (provider, currency_pair, user_id)

**Files to Modify:**
- `app/services/rate_fetcher.py`
- `app/services/rate_processor.py`
- `app/decorators.py`
- `app/api/rates.py`

**Acceptance Criteria:**
- Traces visible in Jaeger UI
- Spans properly nested and correlated
- Attributes populated correctly
- Errors recorded in traces

#### 1.3 Structured Logging Setup
- [ ] Configure loguru for structured JSON logging
- [ ] Add context to all log messages (user_id, request_id, etc.)
- [ ] Ensure logs sent to CloudWatch in JSON format

**Files to Modify:**
- `app/__init__.py` (configure loguru)
- All files with logging

**Acceptance Criteria:**
- Logs in JSON format in CloudWatch
- Searchable by structured fields
- Request ID correlation works

---

### Phase 2: Worker & Database Monitoring (Week 2)

#### 2.1 Celery Monitoring
- [ ] Add OpenTelemetry instrumentation to Celery
- [ ] Implement Celery signal handlers for metrics
- [ ] Add task lifecycle logging
- [ ] Monitor queue depth via Redis

**Files to Create/Modify:**
- `tasks/celery_app.py` (add instrumentation)
- `tasks/monitoring.py` (new file for signals)
- `app/services/celery_metrics.py` (new file)

**Acceptance Criteria:**
- Task metrics in Prometheus
- Task traces in Jaeger
- Queue depth visible

#### 2.2 Database Monitoring
- [ ] Add SQLAlchemy pool metrics
- [ ] Create database monitoring queries
- [ ] Set up slow query logging
- [ ] Monitor connection health

**Files to Create:**
- `monitoring/database_metrics.py` (new file)
- `app/extensions.py` (add pool metrics)

**Acceptance Criteria:**
- Connection pool metrics in Prometheus
- Slow queries logged
- Lock monitoring active

#### 2.3 Redis Monitoring
- [ ] Create Redis metrics collection script
- [ ] Monitor cache hit/miss rates
- [ ] Monitor queue operations
- [ ] Track connection pool health

**Files to Create:**
- `monitoring/redis_metrics.py` (new file)

**Acceptance Criteria:**
- Redis metrics in Prometheus
- Cache efficiency visible
- Connection health tracked

---

### Phase 3: Dashboards & Alerts (Week 3)

#### 3.1 Grafana Dashboards
- [ ] Create Application Performance dashboard
- [ ] Create Business Metrics dashboard
- [ ] Create Infrastructure dashboard
- [ ] Create Database Performance dashboard
- [ ] Create Celery Worker dashboard

**Files to Create:**
- `grafana/dashboards/application-performance.json`
- `grafana/dashboards/business-metrics.json`
- `grafana/dashboards/infrastructure.json`
- `grafana/dashboards/database-performance.json`
- `grafana/dashboards/celery-workers.json`

#### 3.2 Alert Rules
- [ ] High error rate (>5% for 5 minutes)
- [ ] High latency (p95 >1s for 5 minutes)
- [ ] Provider failures (all providers down)
- [ ] Database connection saturation (>80%)
- [ ] Memory usage high (>80%)
- [ ] Task failure rate high (>10%)
- [ ] Queue depth growing (>1000 tasks)

**Files to Create:**
- `prometheus/alerts/application.yml`
- `prometheus/alerts/infrastructure.yml`
- `prometheus/alerts/workers.yml`

**Acceptance Criteria:**
- All dashboards functional
- Alerts firing correctly
- Alert notifications working

---

### Phase 4: Advanced Monitoring (Week 4)

#### 4.1 Business Intelligence
- [ ] Track business KPIs
- [ ] Monitor rate update frequency
- [ ] Track API usage by customer
- [ ] Monitor rate spread accuracy

#### 4.2 SLO/SLI Definition
- [ ] Define service level objectives
- [ ] Implement SLI tracking
- [ ] Create error budget monitoring

#### 4.3 Distributed Tracing Enhancement
- [ ] Add trace sampling configuration
- [ ] Implement trace context propagation to Celery
- [ ] Add trace baggage for business context

---

## 📝 Implementation Tracking

### Phase 1 Progress: 0% Complete
- [ ] Metrics implementation: 0/6 files
- [ ] Tracing implementation: 0/4 files
- [ ] Logging setup: 0/1 tasks

### Phase 2 Progress: 0% Complete
- [ ] Celery monitoring: 0/3 tasks
- [ ] Database monitoring: 0/4 tasks
- [ ] Redis monitoring: 0/4 tasks

### Phase 3 Progress: 0% Complete
- [ ] Dashboards: 0/5 created
- [ ] Alerts: 0/7 configured

### Phase 4 Progress: 0% Complete
- [ ] Business intelligence: 0/4 tasks
- [ ] SLO/SLI: 0/3 tasks
- [ ] Advanced tracing: 0/3 tasks

---

## 🎯 Success Metrics

### Application Layer
- ✅ 100% of API endpoints have metrics
- ✅ 100% of business operations traced
- ✅ All logs structured and searchable
- ✅ P95 latency <500ms
- ✅ Error rate <1%

### Worker Layer
- ✅ 100% task success rate
- ✅ Queue depth <100 tasks
- ✅ Task duration <2 minutes

### Database Layer
- ✅ Query latency <50ms (p95)
- ✅ Connection pool <70% utilization
- ✅ Zero deadlocks

### Infrastructure Layer
- ✅ CPU utilization <70%
- ✅ Memory utilization <80%
- ✅ Zero OOM kills

---

## 📚 Resources

### Documentation
- OpenTelemetry Python SDK: https://opentelemetry.io/docs/instrumentation/python/
- Prometheus Best Practices: https://prometheus.io/docs/practices/
- Grafana Dashboard Design: https://grafana.com/docs/grafana/latest/dashboards/

### Tools
- OpenTelemetry Collector
- Prometheus
- Grafana
- Jaeger
- CloudWatch Logs/Metrics
- ECS Container Insights

---

## 🔄 Review Schedule

- **Daily:** Check critical alerts
- **Weekly:** Review dashboard metrics, update this checklist
- **Monthly:** Review and adjust SLOs, optimize dashboards
- **Quarterly:** Full monitoring stack review

---

**Next Review Date:** 2025-11-10
**Owner:** DevOps/SRE Team
**Status:** 🟡 In Progress

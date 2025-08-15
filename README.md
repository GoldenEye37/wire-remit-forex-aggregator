# WireRemit Forex Aggregator

A comprehensive forex rate aggregation system that fetches rates from multiple providers, applies markup, and provides real-time and historical rate data via REST APIs.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Authentication Flow](#authentication-flow)
- [Rate Aggregation Logic](#rate-aggregation-logic)
- [Celery Tasks](#celery-tasks)
- [Database Schema](#database-schema)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

## Features

- **Multi-Provider Rate Fetching**: Fetches forex rates from ExchangeRate API, Polygon, and FixerIO
- **Real-time Aggregation**: Calculates average rates with configurable markup
- **Historical Data**: Stores and provides access to historical rate data
- **JWT Authentication**: Secure API access with role-based permissions
- **Admin Panel**: Currency pair management and markup configuration
- **Automated Tasks**: Hourly rate refresh using Celery Beat
- **Comprehensive APIs**: RESTful endpoints for rates, authentication, and administration
- **Rate Inversion**: Supports querying any currency as base or target


## Prerequisites

- **Python 3.11+**
- **PostgreSQL 12+**
- **Redis 6+** (for Celery broker)
- **Git**

### External APIs (Optional)
- ExchangeRate API key
- Polygon API key  
- FixerIO API key

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/wiremit-forex-aggregator.git
cd wiremit-forex-aggregator
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Database Setup

```bash
# Create PostgreSQL database
createdb wiremit_forex

# Or using psql
psql -U postgres
CREATE DATABASE wiremit_forex;
\q
```

### 5. Environment Configuration

Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/wiremit_forex

# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-super-secret-key-change-in-production

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
JWT_EXPIRATION_HOURS=24

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# API Keys (Optional)
EXCHANGE_RATE_API_KEY=your-exchangerate-api-key
POLYGON_API_KEY=your-polygon-api-key
FIXER_IO_API_KEY=your-fixer-io-api-key

# Application Settings
APP_HOST=localhost
APP_PORT=5000
```

### 6. Database Migration

```bash
# Initialize migrations (first time only)
flask db init

# Create migration
flask db migrate -m "Initial migration"

# Apply migration
flask db upgrade
```

### 7. Seed Database (Optional)

```bash
# Start Flask shell
flask shell

# Add sample data
from app.models import Provider, CurrencyPair, User
from app.extensions import db
from app.services.auth_service import AuthService

# Create providers
exchange_provider = Provider(name="ExchangeRateAPI", provider_class="ExchangeRateClient", is_active=True)
polygon_provider = Provider(name="Polygon", provider_class="PolygonClient", is_active=True)
db.session.add_all([exchange_provider, polygon_provider])

# Create currency pairs
pairs = [
    CurrencyPair(base_currency="USD", target_currency="ZAR", markup_percentage=0.05),
    CurrencyPair(base_currency="USD", target_currency="GBP", markup_percentage=0.03),
    CurrencyPair(base_currency="EUR", target_currency="USD", markup_percentage=0.04),
]
db.session.add_all(pairs)

# Create admin user
auth_service = AuthService()
hashed_password = auth_service.hash_password("admin123")
admin_user = User(
    email="admin@wiremit.com",
    password_hash=hashed_password,
    first_name="Admin",
    last_name="User",
    is_admin=True,
    is_active=True
)
db.session.add(admin_user)

db.session.commit()
exit()
```

## Configuration

### Core Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | Required |
| `CELERY_BROKER_URL` | Redis URL for Celery | `redis://localhost:6379/0` |
| `JWT_EXPIRATION_HOURS` | JWT token expiration | 24 hours |

### Provider Settings

Configure API keys for external providers in `.env`:

```env
EXCHANGE_RATE_API_KEY=your-key
POLYGON_API_KEY=your-key
FIXER_IO_API_KEY=your-key
```

## Running the Application

### 1. Start Required Services

```bash
# Start PostgreSQL (if not running)
brew services start postgresql

# Start Redis
redis-server
# Or: brew services start redis
```

### 2. Start Flask Application

```bash
python run.py
```

The application will be available at `http://localhost:5000`

### 3. Start Celery Services

#### Option A: Using Shell Scripts (Recommended)

```bash
# Make scripts executable
chmod +x celery.sh celery_beat.sh celery_manager.sh

# Start worker (in terminal 1)
./celery.sh

# Start beat scheduler (in terminal 2)  
./celery_beat.sh
```

#### Option B: Manual Commands

```bash
# Terminal 1: Start Celery worker
celery -A tasks.celery_app worker --loglevel=info

# Terminal 2: Start Celery beat
celery -A tasks.celery_app beat --loglevel=info

# Terminal 3: Start Flower monitoring (optional)
celery -A tasks.celery_app flower --port=5555
```

## API Documentation

Swagger UI: http://localhost:5000/docs/
OpenAPI JSON: http://localhost:5000/swagger.json

## Authentication Flow

The system uses JWT (JSON Web Tokens) for authentication with role-based access control.

### 1. User Registration

```bash
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

**Response:**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_admin": false
  },
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 2. User Login

```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

### 3. Protected Endpoints

Include the JWT token in the Authorization header:

```bash
curl -X GET http://localhost:5000/rates/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 4. Admin Endpoints

Admin endpoints require `is_admin: true` in the user record:

```bash
curl -X POST http://localhost:5000/admin/currency-pairs \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "base_currency": "USD",
    "target_currency": "EUR",
    "markup_percentage": 0.03
  }'
```

### Authentication Decorators

The system uses three authentication decorators:

- `@require_jwt` - Requires valid JWT token
- `@require_admin` - Requires admin privileges (use after `@require_jwt`)
- `@require_jwt_admin` - Combined JWT and admin check

## Rate Aggregation Logic

The system implements a sophisticated rate aggregation pipeline:

### 1. Rate Fetching Process

```python
# Triggered every hour by Celery Beat
@celery.task
def refresh_rates():
    processor = RateProcessorService()
    processor.process_rates_for_currencies()
```

### 2. Provider Integration

Each provider implements the `BaseProviderClient` interface:

```python
class ExchangeRateClient(BaseProviderClient):
    def get_rates(self, base_currency: str) -> Dict[str, Any]:
        # Fetch rates from ExchangeRate API
        # Returns: {"conversion_rates": {"EUR": 0.85, "GBP": 0.73}}
```

### 3. Rate Processing Pipeline

#### Step 1: Fetch Raw Rates
```python
# Group currency pairs by base currency
grouped_pairs = {"USD": ["EUR", "GBP"], "EUR": ["USD"]}

# Fetch from each provider
exchange_rates = exchange_client.get_rates("USD")
polygon_rates = polygon_client.get_rates("USD", "EUR")
```

#### Step 2: Normalize and Save
```python
# Convert to Rate objects
rate = Rate(
    currency_pair_id=pair.id,
    buy_rate=rate_value,
    sell_rate=rate_value,
    fetched_at=timestamp,
    provider_id=provider.id
)
```

#### Step 3: Aggregate Rates
```python
# Calculate averages per currency pair
average_buy = sum(rates.buy_rate) / len(rates)
average_sell = sum(rates.sell_rate) / len(rates)

# Apply markup
final_buy = average_buy * (1 + markup_percentage)
final_sell = average_sell * (1 - markup_percentage)

# Save aggregated rate
aggregated_rate = AggregatedRate(
    currency_pair_id=pair.id,
    average_buy_rate=average_buy,
    average_sell_rate=average_sell,
    final_buy_rate=final_buy,
    final_sell_rate=final_sell,
    markup_percentage=markup_percentage,
    provider_count=len(providers),
    aggregated_at=datetime.utcnow(),
    expires_at=datetime.utcnow() + timedelta(hours=1)
)
```

### 4. Rate Inversion Logic

For currency pairs not directly available, the system inverts existing rates:

```python
# If USD/ZAR exists but ZAR/USD is requested
if target_currency_in_base_position:
    inverted_buy_rate = 1 / original_sell_rate
    inverted_sell_rate = 1 / original_buy_rate
```

### 5. Markup Configuration

Markup can be configured at three levels:
- **Global**: Applied to all pairs
- **Per Pair**: Individual markup per currency pair  

### Query Parameters

#### Historical Rates (`/rates/historical`)
- `base` - Filter by base currency
- `target` - Filter by target currency  
- `from_date` - Start date (YYYY-MM-DD)
- `to_date` - End date (YYYY-MM-DD)
- `limit` - Max records (default: 100, max: 1000)
- `order` - Sort order ('asc' or 'desc')

## Celery Tasks

### Available Tasks

1. **`refresh_rates`** - Scheduled task that runs every hour

### Task Configuration

```python
# Scheduled task configuration
beat_schedule = {
    'refresh-rates-every-hour': {
        'task': 'tasks.rate_refresh.refresh_rates',
        'schedule': 3600.0,  # Every hour
        'options': {
            'expires': 3600,  # Task expires in 1 hour
        }
    },
}
```

### Manual Task Execution

```bash
# Trigger manual refresh
./celery_manager.sh manual-refresh

# Or using Python
python -c "
from tasks.rate_refresh import refresh_rates_manual
result = refresh_rates_manual.delay()
print(f'Task ID: {result.id}')
"
```

### Monitoring

- **Flower UI**: `http://localhost:5555` (if running)
- **Celery inspect**: `celery -A tasks.celery_app inspect active`
- **Logs**: Check `/tmp/celery/worker.log` and `/tmp/celery/beat.log`

## Database Schema

### Core Tables

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- Currency pairs table
CREATE TABLE currency_pairs (
    id SERIAL PRIMARY KEY,
    base_currency VARCHAR(3) NOT NULL,
    target_currency VARCHAR(3) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    markup_percentage DECIMAL(5,4) DEFAULT 0.1000,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(base_currency, target_currency)
);

-- Providers table
CREATE TABLE providers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    provider_class VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Raw rates table
CREATE TABLE rates (
    id SERIAL PRIMARY KEY,
    currency_pair_id INTEGER REFERENCES currency_pairs(id),
    provider_id INTEGER REFERENCES providers(id),
    buy_rate DECIMAL(18,8) NOT NULL,
    sell_rate DECIMAL(18,8) NOT NULL,
    fetched_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Aggregated rates table
CREATE TABLE aggregated_rates (
    id SERIAL PRIMARY KEY,
    currency_pair_id INTEGER REFERENCES currency_pairs(id),
    average_buy_rate DECIMAL(18,8) NOT NULL,
    average_sell_rate DECIMAL(18,8) NOT NULL,
    final_buy_rate DECIMAL(18,8) NOT NULL,
    final_sell_rate DECIMAL(18,8) NOT NULL,
    markup_percentage DECIMAL(5,4) NOT NULL,
    provider_count INTEGER NOT NULL,
    aggregated_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Indexes

```sql
-- Performance indexes
CREATE INDEX idx_rates_pair_time ON rates(currency_pair_id, fetched_at);
CREATE INDEX idx_rates_provider_time ON rates(provider_id, fetched_at);
CREATE INDEX idx_aggregated_pair_time ON aggregated_rates(currency_pair_id, aggregated_at);
```

## Development

### Project Structure

```
wiremit-forex-aggregator/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── models.py                # SQLAlchemy models
│   ├── extensions.py            # Flask extensions
│   ├── api/                     # API blueprints
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── rates.py            # Rate endpoints  
│   │   └── admin.py            # Admin endpoints
│   ├── services/               # Business logic
│   │   ├── auth_service.py     # Authentication service
│   │   ├── rate_processor.py   # Rate processing service
│   │   ├── user_service.py     # User management
│   │   └── providers/          # Rate provider clients
│   └── decorators/             # Custom decorators
│       └── auth.py             # JWT decorators
├── tasks/                      # Celery tasks
│   ├── celery_app.py          # Celery configuration
│   └── rate_refresh.py        # Rate refresh tasks
├── migrations/                 # Database migrations
├── tests/                      # Test files
├── config.py                   # Configuration
├── run.py                      # Application entry point
└── requirements.txt            # Dependencies
```

### Adding New Providers

1. Create provider client in `app/services/providers/`:

```python
from .base_provider import BaseProviderClient

class NewProviderClient(BaseProviderClient):
    def get_rates(self, base_currency: str) -> Dict[str, Any]:
        # Implement rate fetching logic
        pass
    
    def health_check(self) -> Dict[str, Any]:
        # Implement health check
        pass
```

2. Register in provider factory:

```python
# app/services/providers/provider_factory.py
PROVIDER_MAP = {
    "new_provider": NewProviderClient,
    # ... existing providers
}
```

3. Add to database:

```sql
INSERT INTO providers (name, provider_class, is_active) 
VALUES ('NewProvider', 'NewProviderClient', true);
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

### Code Quality

```bash
# Install development dependencies
pip install black isort flake8 ruff

# Format code
black app/ tasks/
isort app/ tasks/

# Lint code
ruff check app/ tasks/
flake8 app/ tasks/
```

## Troubleshooting

### Common Issues

#### 1. Celery Configuration Error
```
ImproperlyConfigured: Cannot mix new and old setting keys
```
**Solution**: Ensure all Celery config uses new format (no `CELERY_` prefix in app config)

#### 2. Database Connection Error
```
sqlalchemy.exc.OperationalError: could not connect to server
```
**Solution**: 
- Verify PostgreSQL is running: `brew services start postgresql`
- Check connection string in `.env`
- Ensure database exists: `createdb wiremit_forex`

#### 3. Redis Connection Error
```
celery.exceptions.InvalidCacheBackendError
```
**Solution**:
- Start Redis: `redis-server` or `brew services start redis`
- Verify Redis URL in `.env`

#### 4. Import Errors
```
ModuleNotFoundError: No module named 'app'
```
**Solution**:
- Ensure virtual environment is activated
- Run commands from project root
- Set `PYTHONPATH`: `export PYTHONPATH=$PWD`

#### 5. JWT Token Errors
```
{"error": "Invalid or expired token"}
```
**Solution**:
- Check token format: `Bearer <token>`
- Verify JWT_SECRET_KEY in `.env`
- Ensure token hasn't expired

### Debug Mode

Enable debug logging:

```python
# In config.py
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set environment variable
export FLASK_ENV=development
```

### Health Checks

```bash
# Check application health
curl http://localhost:5000/

# Check database connection
flask shell -c "from app.extensions import db; print(db.engine.execute('SELECT 1').scalar())"

# Check Redis connection
redis-cli ping

# Check Celery worker
celery -A tasks.celery_app inspect active
```

### Performance Monitoring

1. **Database Queries**: Use Flask-SQLAlchemy's logging
2. **Celery Tasks**: Monitor via Flower UI
3. **API Response Times**: Implement request logging middleware
4. **Memory Usage**: Monitor worker processes

### Backup & Recovery

```bash
# Database backup
pg_dump wiremit_forex > backup.sql

# Database restore
psql wiremit_forex < backup.sql

# Redis backup
redis-cli BGSAVE
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please contact:
- Email: dhimbaleon356@gmail.com

---

**Version**: 1.0.0  
**Last Updated**: August 15, 2025

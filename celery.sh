#!/bin/bash
# Celery Worker startup script

set -e  # Exit on any error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

error() {
    echo -e "${RED}Error: $1${NC}" >&2
    exit 1
}

warn() {
    echo -e "${YELLOW}Warning: $1${NC}"
}

info() {
    echo -e "${GREEN}$1${NC}"
}

# Change to script directory
cd "$(dirname "${BASH_SOURCE[0]}")" || error "Could not change to script directory"

# Check dependencies
[ -d ".venv" ] || error "Virtual environment not found. Run: python -m venv .venv"

# Activate virtual environment
source .venv/bin/activate || error "Could not activate virtual environment"

# Check Redis (non-blocking)
if ! redis-cli ping >/dev/null 2>&1; then
    warn "Redis not running. Start with: redis-server"
fi

# Check Celery installation
python -c "import celery" 2>/dev/null || error "Celery not installed. Run: pip install celery[redis]"

# Set environment
export FLASK_APP=run.py FLASK_ENV=development

# Start Celery
info "Starting Celery Worker..."
trap 'echo -e "\n${YELLOW}Shutting down...${NC}"; exit 0' INT

celery -A tasks.celery_app.celery worker \
    --loglevel=info \
    --concurrency=4 \
    --prefetch-multiplier=1 \
    --without-gossip \
    --without-mingle \
    --without-heartbeat
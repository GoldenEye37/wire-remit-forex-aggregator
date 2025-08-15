#!/bin/bash
# Celery Worker startup script

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Celery Worker...${NC}"
echo -e "${YELLOW}Project Root: $PROJECT_ROOT${NC}"

# Change to project directory
cd "$PROJECT_ROOT" || {
    echo -e "${RED}Error: Could not change to project directory${NC}"
    exit 1
}

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}Error: Virtual environment not found at .venv${NC}"
    echo -e "${YELLOW}Please create a virtual environment first:${NC}"
    echo "python -m venv .venv"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate || {
    echo -e "${RED}Error: Could not activate virtual environment${NC}"
    exit 1
}

# Check if Redis is running
echo -e "${YELLOW}Checking Redis connection...${NC}"
redis-cli ping > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${RED}Warning: Redis server is not running${NC}"
    echo -e "${YELLOW}Please start Redis server first:${NC}"
    echo "redis-server"
    echo ""
    echo -e "${YELLOW}Attempting to start Celery anyway...${NC}"
fi

# Export Flask app for any imports
export FLASK_APP=run.py
export FLASK_ENV=development

# Check if Celery is installed
python -c "import celery" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Celery is not installed${NC}"
    echo -e "${YELLOW}Please install Celery:${NC}"
    echo "pip install celery[redis]"
    exit 1
fi

echo -e "${GREEN}Starting Celery Worker with the following configuration:${NC}"
echo -e "${YELLOW}  - App: tasks.celery_app.celery${NC}"
echo -e "${YELLOW}  - Log Level: info${NC}"
echo -e "${YELLOW}  - Concurrency: auto${NC}"
echo ""

# Set trap to handle Ctrl+C
trap 'echo -e "\n${YELLOW}Shutting down Celery Worker...${NC}"; exit 0' INT

# Start Celery Worker
celery -A tasks.celery_app.celery worker \
    --loglevel=info \
    --concurrency=4 \
    --prefetch-multiplier=1 \
    --without-gossip \
    --without-mingle \
    --without-heartbeat

echo -e "${GREEN}Celery Worker stopped${NC}"
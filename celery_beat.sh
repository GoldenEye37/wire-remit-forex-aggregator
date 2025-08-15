#!/bin/bash
# Celery Beat scheduler startup script

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Celery Beat Scheduler...${NC}"
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
    echo -e "${YELLOW}Attempting to start Celery Beat anyway...${NC}"
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

# Create temp directory for beat files if it doesn't exist
TEMP_DIR="/tmp/celery"
mkdir -p "$TEMP_DIR"

# Define beat schedule and PID file paths
BEAT_SCHEDULE="$TEMP_DIR/celerybeat-schedule"
BEAT_PID="$TEMP_DIR/celerybeat.pid"

# Clean up old beat files
if [ -f "$BEAT_PID" ]; then
    echo -e "${YELLOW}Cleaning up old beat PID file...${NC}"
    rm -f "$BEAT_PID"
fi

echo -e "${GREEN}Starting Celery Beat with the following configuration:${NC}"
echo -e "${YELLOW}  - App: tasks.celery_app.celery${NC}"
echo -e "${YELLOW}  - Log Level: info${NC}"
echo -e "${YELLOW}  - Schedule File: $BEAT_SCHEDULE${NC}"
echo -e "${YELLOW}  - PID File: $BEAT_PID${NC}"
echo ""

# Set trap to handle Ctrl+C
trap 'echo -e "\n${YELLOW}Shutting down Celery Beat...${NC}"; rm -f "$BEAT_PID"; exit 0' INT

# Start Celery Beat
celery -A tasks.celery_app.celery beat \
    --loglevel=info \
    --schedule="$BEAT_SCHEDULE" \
    --pidfile="$BEAT_PID"

echo -e "${GREEN}Celery Beat stopped${NC}"

# Clean up
rm -f "$BEAT_PID"
#!/bin/bash
# Run Wiki Service test suite
# This script runs the full Wiki Service test suite for manual execution

set -e

# Force unbuffered output
export PYTHONUNBUFFERED=1

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT" || exit 1

# Verify project structure
if [ ! -f "requirements.txt" ] || [ ! -d "services/wiki" ]; then
    echo -e "${RED}Error: Not in Arcadium project root${NC}" >&2
    exit 1
fi

# Check pytest
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest not found${NC}" >&2
    echo "Install dependencies: pip install -r requirements.txt" >&2
    exit 1
fi

# Set test environment
export FLASK_ENV=testing

# Load .env file if it exists
if [ -f "services/wiki/.env" ]; then
    # Load environment variables using Python dotenv
    ENV_EXPORTS=$(cd services/wiki && python -c "
import os
from dotenv import load_dotenv
load_dotenv()
for key in ['DATABASE_URL', 'TEST_DATABASE_URL', 'arcadium_user', 'arcadium_pass', 'DB_HOST', 'DB_PORT', 'DB_NAME', 'TEST_DB_NAME']:
    value = os.environ.get(key)
    if value:
        value = value.replace('\"', '\\\\\"').replace('\$', '\\\\\$').replace('\`', '\\\\\`').replace('\\\\', '\\\\\\\\')
        print(f'export {key}=\"{value}\"')
" 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$ENV_EXPORTS" ]; then
        eval "$ENV_EXPORTS"
    fi
fi

# Change to wiki service directory
cd services/wiki || exit 1

# Show database info (without password)
echo -e "${BLUE}================================================================================${NC}"
echo -e "${BLUE}Running Wiki Service Tests${NC}"
echo -e "${BLUE}================================================================================${NC}"
echo ""

if [ -n "$TEST_DATABASE_URL" ]; then
    DB_INFO=$(echo "$TEST_DATABASE_URL" | sed 's|postgresql://[^:]*:.*@|postgresql://***:***@|')
    echo -e "Database: ${GREEN}$DB_INFO${NC}"
elif [ -n "$DATABASE_URL" ]; then
    DB_INFO=$(echo "$DATABASE_URL" | sed 's|postgresql://[^:]*:.*@|postgresql://***:***@|')
    echo -e "Database: ${GREEN}$DB_INFO${NC}"
elif [ -n "$arcadium_user" ]; then
    echo -e "Database: ${GREEN}$arcadium_user@${TEST_DB_NAME:-arcadium_testing_wiki}${NC}"
else
    echo -e "${YELLOW}⚠ Using default database configuration${NC}"
fi
echo ""

# Run pytest with cleaner output
echo -e "${BLUE}Running pytest...${NC}"
echo ""

if pytest --tb=short -v --durations=10 --color=yes; then
    echo ""
    echo -e "${BLUE}================================================================================${NC}"
    echo -e "${GREEN}[OK] All tests passed!${NC}"
    echo -e "${BLUE}================================================================================${NC}"
    exit 0
else
    EXIT_CODE=$?
    echo ""
    echo -e "${BLUE}================================================================================${NC}"
    echo -e "${RED}[X] Tests failed (exit code: $EXIT_CODE)${NC}"
    echo -e "${BLUE}================================================================================${NC}"
    exit $EXIT_CODE
fi

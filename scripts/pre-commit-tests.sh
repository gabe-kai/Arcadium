#!/bin/bash
# Pre-commit hook to run Wiki Service tests
# This hook runs the Wiki Service test suite to catch failures before committing

# Don't exit on error immediately - we want to see what's happening
set +e

# Force output to be unbuffered
export PYTHONUNBUFFERED=1

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print with immediate flush
print_step() {
    if [ "$1" = "-e" ]; then
        shift
        echo -e "$@" >&2
    else
        echo "$@" >&2
    fi
    # Force flush stdout/stderr
    exec >&2
}

print_step ""
print_step "=========================================="
print_step "Running pre-commit tests..."
print_step "=========================================="
print_step ""

# Get the project root (where .git is located)
# This script is called from .git/hooks, so we need to go up two levels
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT" || exit 1

# Check if we're in the Arcadium project root
print_step -e "${GREEN}[CHECK]${NC} Verifying project structure..."
if [ ! -f "requirements.txt" ] || [ ! -d "services/wiki" ]; then
    print_step -e "${YELLOW}Warning: Not in Arcadium project root. Skipping tests.${NC}"
    exit 0
fi
print_step "  ✓ Project structure OK"

# Check if pytest is available
print_step -e "${GREEN}[CHECK]${NC} Checking pytest availability..."
if ! command -v pytest &> /dev/null; then
    print_step -e "${YELLOW}Warning: pytest not found. Skipping tests.${NC}"
    print_step "Install dependencies: pip install -r requirements.txt"
    exit 0
fi
PYTEST_VERSION=$(pytest --version 2>&1)
print_step "  ✓ pytest found: $PYTEST_VERSION"

# Check if PostgreSQL is available (basic check)
print_step -e "${GREEN}[CHECK]${NC} Checking PostgreSQL tools..."
if ! command -v psql &> /dev/null; then
    print_step -e "  ${YELLOW}⚠ psql not found. Database may not be available.${NC}"
    print_step "  Tests may fail if database is not accessible."
else
    print_step "  ✓ psql found"
fi

# Set test environment
print_step ""
print_step -e "${GREEN}[1/4]${NC} Setting FLASK_ENV=testing..."
export FLASK_ENV=testing
print_step "  ✓ FLASK_ENV set to testing"

# Load .env file from services/wiki directory if it exists
# This ensures we use the correct database credentials from the .env file
print_step ""
print_step -e "${GREEN}[2/4]${NC} Loading environment variables..."
if [ -f "services/wiki/.env" ]; then
    print_step "  → Found services/wiki/.env file"
    print_step "  → Loading variables using Python dotenv..."

    # Use Python to load .env file (handles quotes, comments, and special characters correctly)
    # Separate stderr (status messages) from stdout (export commands)
    ENV_STATUS=$(cd services/wiki && python -u -c "
import os
import sys
try:
    from dotenv import load_dotenv
    load_dotenv()

    # Export all relevant variables for shell (to stdout)
    vars_found = []
    for key in ['DATABASE_URL', 'TEST_DATABASE_URL', 'arcadium_user', 'arcadium_pass', 'DB_HOST', 'DB_PORT', 'DB_NAME', 'TEST_DB_NAME']:
        value = os.environ.get(key)
        if value:
            vars_found.append(key)
            # Escape special characters for shell
            value = value.replace('\"', '\\\\\"').replace('\$', '\\\\\$').replace('\`', '\\\\\`').replace('\\\\', '\\\\\\\\')
            print(f'export {key}=\"{value}\"')

    # Status message to stderr
    if vars_found:
        vars_str = ', '.join(vars_found)
        print(f'Loaded {len(vars_found)} variables: {vars_str}', file=sys.stderr)
    else:
        print('No database variables found in .env', file=sys.stderr)
except ImportError as e:
    print(f'ERROR: python-dotenv not installed: {e}', file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f'ERROR loading .env: {e}', file=sys.stderr)
    sys.exit(1)
" 2> >(while read line; do print_step "    $line"; done))

    if [ $? -eq 0 ]; then
        # Now get the export commands (stdout only)
        ENV_EXPORTS=$(cd services/wiki && python -u -c "
import os
from dotenv import load_dotenv
load_dotenv()
for key in ['DATABASE_URL', 'TEST_DATABASE_URL', 'arcadium_user', 'arcadium_pass', 'DB_HOST', 'DB_PORT', 'DB_NAME', 'TEST_DB_NAME']:
    value = os.environ.get(key)
    if value:
        value = value.replace('\"', '\\\\\"').replace('\$', '\\\\\$').replace('\`', '\\\\\`').replace('\\\\', '\\\\\\\\')
        print(f'export {key}=\"{value}\"')
")
        eval "$ENV_EXPORTS"
        print_step "  ✓ Environment variables loaded"
    else
        print_step -e "  ${RED}✗ Failed to load .env file${NC}"
        exit 1
    fi
else
    print_step -e "  ${YELLOW}⚠ No .env file found at services/wiki/.env${NC}"
    print_step "  → Will use environment variables or defaults"
fi

# Change to wiki service directory
print_step ""
print_step -e "${GREEN}[3/4]${NC} Changing to services/wiki directory..."
if ! cd services/wiki; then
    print_step -e "  ${RED}✗ Failed to change to services/wiki directory${NC}"
    exit 1
fi
print_step "  ✓ Changed to services/wiki"

# Show database connection info (without password)
print_step ""
print_step "Database configuration:"
if [ -n "$TEST_DATABASE_URL" ]; then
    DB_INFO=$(echo "$TEST_DATABASE_URL" | sed 's|postgresql://[^:]*:.*@|postgresql://***:***@|')
    print_step "  → Using TEST_DATABASE_URL: $DB_INFO"
elif [ -n "$DATABASE_URL" ]; then
    DB_INFO=$(echo "$DATABASE_URL" | sed 's|postgresql://[^:]*:.*@|postgresql://***:***@|')
    print_step "  → Using DATABASE_URL: $DB_INFO"
elif [ -n "$arcadium_user" ]; then
    print_step "  → Using arcadium_user: $arcadium_user"
    print_step "  → Database: ${TEST_DB_NAME:-arcadium_testing_wiki}"
else
    print_step -e "  ${YELLOW}⚠ No database credentials found${NC}"
fi

# Run tests
print_step ""
print_step -e "${GREEN}[4/4]${NC} Running Wiki Service tests..."
print_step "  → This may take a few minutes..."
print_step "  → Starting pytest..."
print_step ""

# Run pytest with progress indicators
# Use -v for verbose and --tb=short for concise errors
# Remove -q so we see progress
set -e  # Now exit on error
if pytest --tb=short -v --durations=10; then
    print_step ""
    print_step -e "${GREEN}✓ All tests passed!${NC}"
    print_step ""
    exit 0
else
    EXIT_CODE=$?
    print_step ""
    print_step -e "${RED}✗ Tests failed! (exit code: $EXIT_CODE)${NC}"
    print_step ""
    print_step "Please fix failing tests before committing."
    print_step "To skip this check (not recommended), use: git commit --no-verify"
    print_step ""
    exit $EXIT_CODE
fi

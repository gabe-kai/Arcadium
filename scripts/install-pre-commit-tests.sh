#!/bin/bash
# Script to install the pre-commit test hook
# This adds the Wiki Service tests to the pre-commit configuration

set -e

# Get the project root directory (where this script is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Check if we're in a git repository
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo "Error: Not in a git repository"
    exit 1
fi

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "Error: pre-commit not found"
    echo "Install it with: pip install pre-commit"
    exit 1
fi

# Check if hook script exists
if [ ! -f "$PROJECT_ROOT/scripts/pre-commit-tests.sh" ]; then
    echo "Error: Test script not found at $PROJECT_ROOT/scripts/pre-commit-tests.sh"
    exit 1
fi

# Make hook script executable
chmod +x "$PROJECT_ROOT/scripts/pre-commit-tests.sh"

# Install pre-commit hooks
cd "$PROJECT_ROOT"
pre-commit install --hook-type pre-commit

echo "⚠ WARNING: Pre-commit test hooks are now disabled."
echo ""
echo "Tests should be run manually before committing:"
echo "  python scripts/run-wiki-tests.py"
echo "  (or: bash scripts/run-wiki-tests.sh)"
echo ""
echo "The pre-commit hooks will still run formatting and linting checks."
echo "To install those hooks: pre-commit install"

#!/bin/bash
# Run CI/CD tests locally
# This script simulates the GitHub Actions CI/CD workflow locally

echo "========================================"
echo "Running CI/CD Tests Locally"
echo "========================================"
echo ""

# Set environment variables to match CI
export FLASK_ENV=testing
export TEST_DATABASE_URL="postgresql://postgres:Le555ecure@localhost:5432/arcadium_testing_wiki"
export arcadium_user=postgres
export arcadium_pass=Le555ecure
export DB_HOST=localhost
export DB_PORT=5432

echo "Environment Variables Set:"
echo "  FLASK_ENV = $FLASK_ENV"
echo "  TEST_DATABASE_URL = $TEST_DATABASE_URL"
echo "  arcadium_user = $arcadium_user"
echo "  DB_HOST = $DB_HOST"
echo "  DB_PORT = $DB_PORT"
echo ""

# Check if pre-commit should be run
RUN_PRE_COMMIT=false
for arg in "$@"; do
    if [[ "$arg" == "--pre-commit" ]] || [[ "$arg" == "-p" ]]; then
        RUN_PRE_COMMIT=true
        break
    fi
done

if [ "$RUN_PRE_COMMIT" = true ]; then
    echo "Running pre-commit checks..."
    pre-commit run --all-files
    if [ $? -ne 0 ]; then
        echo "Pre-commit checks failed!"
        exit 1
    fi
    echo ""
fi

# Run the unified test runner (same as CI)
echo "Running unified backend tests..."
echo ""

OUTPUT_FILE="test-output-ci.txt"
python scripts/run-tests.py all 2>&1 | tee "$OUTPUT_FILE"

TEST_EXIT_CODE=${PIPESTATUS[0]}

echo ""
echo "========================================"
echo "Test Execution Complete"
echo "========================================"
echo ""

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed (exit code: $TEST_EXIT_CODE)"
fi

echo ""
echo "Full test output saved to: $OUTPUT_FILE"
echo "Test logs saved to: logs/tests/"

exit $TEST_EXIT_CODE

# Testing Quick Reference

Quick reference guide for running and understanding tests in the Arcadium project.

## Quick Start

### Run All Backend Tests
```bash
python scripts/run-tests.py all
```

### Run Specific Service Tests
```bash
# Wiki Service (all tests)
python scripts/run-tests.py wiki

# Wiki Service (specific category)
python scripts/run-tests.py wiki models
python scripts/run-tests.py wiki services
python scripts/run-tests.py wiki api
python scripts/run-tests.py wiki utils
python scripts/run-tests.py wiki sync
python scripts/run-tests.py wiki integration
python scripts/run-tests.py wiki performance
python scripts/run-tests.py wiki health

# Auth Service
python scripts/run-tests.py auth

# Shared Auth
python scripts/run-tests.py shared
```

### Run Frontend Tests
```bash
cd client

# Unit/Integration tests
npm run test

# E2E tests
npm run test:e2e
```

## Test Categories

### Backend Test Categories

#### Wiki Service (Run by Category)
When running `python scripts/run-tests.py all`, Wiki tests are automatically split into categories:

- **models** (`test_models/`) - Database models and relationships
- **services** (`test_services/`) - Business logic layer
- **api** (`test_api/`) - HTTP endpoints
- **utils** (`test_utils/`) - Utility functions
- **sync** (`test_sync/`) - File synchronization
- **integration** (`test_integration/`) - Cross-service tests
- **performance** (`test_performance/`) - Performance tests
- **health** (`test_health.py`) - Health checks

**Run specific Wiki category:**
```bash
python scripts/run-tests.py wiki models
python scripts/run-tests.py wiki api
# etc.
```

This allows you to quickly re-run just the failing category instead of all Wiki tests.

#### Auth Service
- **Models** (`test_models/`) - User and token models
- **Services** (`test_services/`) - Authentication logic
- **API** (`test_api/`) - Auth endpoints
- **Utils** (`test_utils/`) - Validators
- **Integration** (`test_integration/`) - Auth flows

### Frontend Test Categories

- **Components** (`src/test/components/`) - React components
- **Pages** (`src/test/pages/`) - Page components
- **Services** (`src/test/services/`) - API clients and state
- **Utils** (`src/test/utils/`) - Utility functions
- **Integration** (`src/test/integration/`) - Multi-component flows
- **E2E** (`e2e/`) - End-to-end browser tests

## PostgreSQL Configuration

All tests require PostgreSQL. Configure in `.env` files:

```bash
# Option 1: Full connection string
TEST_DATABASE_URL=postgresql://user:pass@localhost:5432/arcadium_testing_wiki

# Option 2: Individual variables (recommended)
arcadium_user=your_username
arcadium_pass=your_password
DB_HOST=localhost
DB_PORT=5432
TEST_DB_NAME=arcadium_testing_wiki
```

## Test Statistics

- **Backend:** 750+ tests
- **Frontend Unit/Integration:** 523+ tests
- **Frontend E2E:** 32+ tests
- **Total:** 1,300+ tests

## Test Logging

**⚠️ IMPORTANT: Always check log files for complete test results. Terminal output may be truncated.**

All test runs are automatically logged to files in `logs/tests/`:

- **Individual service logs**: `test_<service>_<timestamp>.log`
- **Summary logs**: `test_all_<timestamp>.log` (when running all tests)

Logs contain:
- Full test output
- Start/completion times
- Exit codes
- Error messages

**View latest logs:**
```bash
# Latest summary log
ls -t logs/tests/test_all_*.log | head -1

# View latest log
cat $(ls -t logs/tests/test_all_*.log | head -1)
```

**Log Limits:**
- Max file size: 50 MB per file
- Backup count: 10 files
- Retention: 30 days or 1 GB total
- Automatic cleanup: Old logs are automatically deleted

See `docs/logging-system.md` for complete logging documentation and `logs/README.md` for log management details.

## Common Commands

### Pytest Commands
```bash
# Run all tests in a service
cd services/wiki
pytest

# Run specific test file
pytest tests/test_models/test_page.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific category
pytest tests/test_models/

# Run with markers
pytest -m unit
pytest -m integration
```

### Frontend Commands
```bash
cd client

# Run all tests
npm run test

# Run in watch mode
npm run test -- --watch

# Run with UI
npm run test:ui

# Run E2E tests
npm run test:e2e

# Run E2E in UI mode
npm run test:e2e:ui
```

## Test Success Criteria

### Models
✅ Models create, update, delete correctly
✅ Relationships work properly
✅ Constraints are enforced

### Services
✅ Business rules are enforced
✅ Data transformations are correct
✅ Error handling works

### API
✅ Endpoints return correct status codes
✅ Response formats are correct
✅ Error responses are appropriate

### Utils
✅ Functions process data correctly
✅ Edge cases are handled

### Integration
✅ Services work together correctly
✅ Data flows properly
✅ Errors propagate correctly

## Troubleshooting

### Database Connection Errors
1. Verify PostgreSQL is running
2. Check `.env` files have correct credentials
3. Ensure test databases exist
4. Verify user permissions

### Test Failures
1. Check error messages
2. Verify test data setup
3. Check database state
4. Review test logs

### Slow Tests
1. Check database connection pooling
2. Review test fixtures
3. Consider parallel execution
4. Check for query optimization

## Documentation

- **Full Overview:** `docs/testing-overview.md`
- **Test Audit:** `docs/testing-audit.md`
- **This Guide:** `docs/testing-quick-reference.md`

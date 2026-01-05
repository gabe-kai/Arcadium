# Arcadium Project - Testing Overview

## Testing Philosophy

All tests in the Arcadium project use **PostgreSQL** to match production behavior. SQLite is not used for testing to avoid compatibility issues with:
- UUID handling
- Foreign key constraints
- Transaction isolation
- Database-specific features

## Test Organization

Tests are organized into clear categories with specific purposes and success criteria.

### Backend Tests

#### Wiki Service

**Location:** `services/wiki/tests/`

##### Models (`test_models/`)
- **Purpose:** Verify database models, relationships, and constraints
- **What it tests:**
  - Model creation, updates, deletions
  - Foreign key relationships
  - Unique constraints
  - Data validation
  - Cascade behaviors
- **Success Criteria:** All models create, update, delete correctly with proper relationships and constraints enforced

##### Services (`test_services/`)
- **Purpose:** Test business logic and service layer functionality
- **What it tests:**
  - Business rules enforcement
  - Data transformations
  - Validation logic
  - Error handling
  - Service integrations
- **Success Criteria:** Services handle business rules, validation, and data transformations correctly

##### API (`test_api/`)
- **Purpose:** Test HTTP endpoints and request/response handling
- **What it tests:**
  - Route handlers
  - Status codes
  - Request validation
  - Response formats
  - Error responses
  - Authentication/authorization
- **Success Criteria:** All endpoints return correct status codes, data formats, and handle errors appropriately

##### Utils (`test_utils/`)
- **Purpose:** Test utility functions and helpers
- **What it tests:**
  - Data formatting
  - String manipulation
  - Validation helpers
  - Conversion functions
  - Edge case handling
- **Success Criteria:** Utilities process data correctly and handle edge cases

##### Sync (`test_sync/`)
- **Purpose:** Test file synchronization system
- **What it tests:**
  - File watching
  - Content synchronization
  - Conflict detection
  - Merge operations
  - File scanning
- **Success Criteria:** File changes sync to database correctly with proper conflict detection and resolution

##### Integration (`test_integration/`)
- **Purpose:** Test cross-service interactions and end-to-end flows
- **What it tests:**
  - Service communication
  - Data flow between services
  - Complete workflows
  - Error propagation
- **Success Criteria:** Services work together correctly with proper data flow and error handling

##### Performance (`test_performance/`)
- **Purpose:** Test performance characteristics
- **What it tests:**
  - Caching effectiveness
  - Query performance
  - Load handling
  - Response times
- **Success Criteria:** System meets performance requirements under expected load

##### Health (`test_health.py`)
- **Purpose:** Test service health and status endpoints
- **What it tests:**
  - Health check endpoints
  - Status reporting
  - Service availability
- **Success Criteria:** Health endpoints return correct status information

#### Auth Service

**Location:** `services/auth/tests/`

##### Models (`test_models/`)
- **Purpose:** Test authentication data models
- **What it tests:**
  - User model
  - Token models (access, refresh, blacklist)
  - Password history model
  - Relationships and constraints
- **Success Criteria:** Models enforce security constraints and relationships correctly

##### Services (`test_services/`)
- **Purpose:** Test authentication business logic
- **What it tests:**
  - User registration
  - Login/logout
  - Token generation and validation
  - Password management
  - Security policies
- **Success Criteria:** Authentication flows work correctly with proper security measures

##### API (`test_api/`)
- **Purpose:** Test authentication API endpoints
- **What it tests:**
  - Registration endpoints
  - Login endpoints
  - Token management endpoints
  - User management endpoints
  - Rate limiting
  - Security headers
- **Success Criteria:** Endpoints handle authentication correctly with security measures

##### Utils (`test_utils/`)
- **Purpose:** Test validation utilities
- **What it tests:**
  - Password validation
  - Email validation
  - Input sanitization
- **Success Criteria:** Validators catch invalid inputs correctly

##### Integration (`test_integration/`)
- **Purpose:** Test complete authentication flows
- **What it tests:**
  - Full registration flow
  - Full login flow
  - Token refresh flow
  - Password reset flow
- **Success Criteria:** Complete authentication workflows function correctly

#### Shared Auth

**Location:** `shared/auth/tests/`

- **Purpose:** Test shared authentication utilities
- **What it tests:**
  - Token validation
  - Permission checking
  - Service token validation
- **Success Criteria:** Shared utilities work correctly across all services

### Frontend Tests

#### Client Unit/Integration Tests

**Location:** `client/src/test/`

##### Components (`components/`)
- **Purpose:** Test React component rendering and behavior
- **What it tests:**
  - Component rendering
  - User interactions
  - Props handling
  - State management
  - Event handling
- **Success Criteria:** Components render correctly and handle user input appropriately

##### Pages (`pages/`)
- **Purpose:** Test full page components
- **What it tests:**
  - Page rendering
  - Data loading
  - Navigation
  - Error states
  - Loading states
- **Success Criteria:** Pages render with correct data and handle navigation correctly

##### Services (`services/`)
- **Purpose:** Test API clients and service layer
- **What it tests:**
  - API calls
  - Request/response handling
  - Error handling
  - State management
  - Token management
- **Success Criteria:** Services handle API calls and state correctly

##### Utils (`utils/`)
- **Purpose:** Test utility functions
- **What it tests:**
  - Data formatting
  - String manipulation
  - Link handling
  - Markdown processing
- **Success Criteria:** Utilities process data correctly

##### Integration (`integration/`)
- **Purpose:** Test multi-component flows
- **What it tests:**
  - Component interactions
  - Data flow
  - User workflows
- **Success Criteria:** Components work together correctly

#### Client E2E Tests

**Location:** `client/e2e/`

##### E2E (`e2e/`)
- **Purpose:** Test complete user journeys in real browser
- **What it tests:**
  - Full user workflows
  - Browser interactions
  - Navigation flows
  - Form submissions
  - Page viewing
- **Success Criteria:** Complete user workflows function correctly in real browser environment

## Running Tests

### Unified Test Runner

Run all tests with progress tracking:

```bash
python scripts/run-tests.py all
```

**Wiki Test Categories:** Wiki tests are automatically split into 8 categories when running `all`:
- `models` - Database models
- `services` - Business logic
- `api` - HTTP endpoints
- `utils` - Utility functions
- `sync` - File synchronization
- `integration` - Integration tests
- `performance` - Performance tests
- `health` - Health checks

**Run specific Wiki category:**
```bash
python scripts/run-tests.py wiki models  # Run only models tests
python scripts/run-tests.py wiki api     # Run only API tests
```

This allows you to quickly re-run just the failing category instead of all Wiki tests.

**Test Logging:** All test runs are automatically logged to `logs/tests/` with timestamps. Each Wiki category gets its own log file. Logs include full output, timing, and results. See `logs/README.md` for details.

### Individual Service Tests

#### Wiki Service
```bash
cd services/wiki
pytest
```

#### Auth Service
```bash
cd services/auth
pytest
```

#### Frontend Unit/Integration
```bash
cd client
npm run test
```

#### Frontend E2E
```bash
cd client
npm run test:e2e
```

## Test Configuration

### PostgreSQL Setup

All tests require PostgreSQL configuration. Set in `.env` files:

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

### Test Databases

Test databases use the naming convention: `arcadium_testing_<service_name>`

- Wiki: `arcadium_testing_wiki`
- Auth: `arcadium_testing_auth`

## Test Statistics

### Current Coverage

- **Backend:** 750+ tests across Wiki, Auth, and Shared services
- **Frontend Unit/Integration:** 523+ tests
- **Frontend E2E:** 32+ tests
- **Total:** 1,300+ tests

### Test Status

All tests are configured to use PostgreSQL and should pass when:
1. PostgreSQL is running
2. Test databases exist
3. Environment variables are configured correctly
4. Dependencies are installed

## Best Practices

1. **Always use PostgreSQL** - Never use SQLite for testing
2. **Test isolation** - Each test should be independent
3. **Clear naming** - Test names should describe what they test
4. **Documentation** - Complex tests should include comments
5. **Coverage** - Aim for high coverage of critical paths
6. **Performance** - Keep tests fast, use fixtures appropriately

## Troubleshooting

### Database Connection Issues

If tests fail with database connection errors:
1. Verify PostgreSQL is running
2. Check `.env` files have correct credentials
3. Ensure test databases exist
4. Verify database user has proper permissions

### Test Failures

If tests fail:
1. Check error messages for specific failures
2. Verify test data setup
3. Check for database state issues
4. Review test logs for detailed errors

### Slow Tests

If tests are slow:
1. Check database connection pooling settings
2. Review test fixtures for unnecessary setup
3. Consider parallel test execution
4. Check for database query optimization opportunities

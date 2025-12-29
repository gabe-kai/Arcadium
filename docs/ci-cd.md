# CI/CD Documentation

This document describes the Continuous Integration and Continuous Deployment setup for the Arcadium project.

## Overview

The project uses **GitHub Actions** for CI/CD. Currently, CI is configured for the Wiki Service, with plans to expand to other services as they are developed.

## GitHub Actions Workflows

### Wiki Service Tests (Backend)

**Location:** `.github/workflows/wiki-service-tests.yml`

**Purpose:** Runs the complete Wiki Service test suite on every push and pull request.

#### When It Runs

- **Push events:**
  - `main` branch
  - Any `feature/**` branch
- **Pull request events:**
  - PRs targeting `main` branch

#### What It Does

1. **Sets up environment:**
   - Ubuntu latest runner
   - Python 3.11
   - PostgreSQL 14 service container

2. **Installs dependencies:**
   - Upgrades pip
   - Installs root `requirements.txt` dependencies
   - Installs Wiki service dependencies (if `services/wiki/requirements.txt` exists)
   - Caches pip packages for faster subsequent runs

3. **Sets up PostgreSQL:**
   - Starts PostgreSQL 14 container
   - Installs PostgreSQL client tools
   - Creates `arcadium_testing_wiki` database
   - Waits for PostgreSQL to be ready

4. **Runs code quality checks:**
   - Installs and runs pre-commit hooks
   - Validates code formatting (black, isort, ruff)
   - Checks for common issues (trailing whitespace, merge conflicts, etc.)

5. **Runs tests:**
   - Executes `pytest` from `services/wiki` directory
   - Uses PostgreSQL test database (avoids SQLite UUID issues)
   - Generates coverage reports

#### Environment Variables

The workflow sets:
- `FLASK_ENV=testing`
- `TEST_DATABASE_URL=postgresql://arcadium:password@localhost:5432/wiki_test`
  - Or use `arcadium_user` and `arcadium_pass` (will construct TEST_DATABASE_URL automatically)

#### Test Configuration

Tests use PostgreSQL (not SQLite) to:
- Avoid UUID compatibility issues
- Match production database behavior
- Ensure accurate test results

See `services/wiki/tests/conftest.py` for test database configuration.

---

### Client Tests (Frontend)

**Status:** ✅ **CI/CD Configured**.
**Location:** `.github/workflows/client-tests.yml`
**Test Location:** `client/`

The Client uses **Vitest** and **React Testing Library** for unit/integration tests, and **Playwright** for E2E tests.

#### When It Runs

- **Push events:**
  - `main` branch
  - Any `feature/**` branch
- **Pull request events:**
  - PRs targeting `main` branch

#### What It Does

The workflow runs three jobs in parallel:

1. **Unit & Integration Tests:**
   - Sets up Node.js 20
   - Installs dependencies with `npm ci`
   - Runs linting and formatting checks (if configured)
   - Runs Vitest test suite (`npm test -- --run`)
   - Automatically discovers and runs all test files (including new auth tests)
   - Attempts to generate coverage report (optional)
   - All tests are mocked and don't require external services

2. **E2E Tests:**
   - Sets up Node.js 20
   - Installs dependencies
   - Installs Playwright browsers
   - Runs Playwright E2E tests (`npm run test:e2e`)
   - Uploads test report as artifact

3. **Build Check:**
   - Sets up Node.js 20
   - Installs dependencies
   - Builds the client (`npm run build`)
   - Ensures production build succeeds

#### Test Coverage

**Unit & Integration Tests (523+ passing tests):**
- ✅ All React components (Editor, EditorToolbar, Navigation, Layout, Footer, Sidebar, etc.)
- ✅ Page components (PageView, EditPage, SignInPage, HomePage, SearchPage, IndexPage)
- ✅ Comments components (CommentsList, CommentItem, CommentForm) - Phase 5
- ✅ Editor components (Editor, EditorToolbar) - Phase 7: WYSIWYG Editor Integration
- ✅ Metadata form component (MetadataForm) - Phase 8: Page Metadata Editor
- ✅ Utility functions (markdown conversion, link handling, slug generation, syntax highlighting)
- ✅ API service functions (Wiki API, Auth API, Comments API)
- ✅ API client interceptors (request/response handling, token management)
- ✅ Authentication system (AuthContext, auth API, sign-in page, header auth)
- ✅ Routing and navigation
- ✅ Edge cases and error scenarios

**E2E Tests (32+ tests):**
- ✅ Page viewing and content rendering
- ✅ Navigation (breadcrumbs, page navigation, navigation tree)
- ✅ Table of Contents and Backlinks
- ✅ Authentication flow (login, register, sign out)
- ✅ Full user workflows

#### Running Wiki UI Tests Locally

From the `client/` directory:

```bash
# Install dependencies (first time)
npm install

# Run all tests
npm test

# Run tests with UI
npm run test:ui

# Run with coverage
npm run test:coverage
```

#### What’s Currently Covered

- App shell renders (React + Router + layout)
- Basic routing (home, page view, search)
- Axios API client configuration

Future CI work (see **Planned CI/CD Features** below) will add:
- A GitHub Actions workflow for the Wiki UI (running `npm test`)
- Optional build checks (`npm run build`) for the client

## Running CI Tests Locally

To verify tests will pass in CI before pushing, replicate the CI environment locally:

### Prerequisites

1. **PostgreSQL running locally:**
   - Host: `localhost`
   - Port: `5432`
   - User: `postgres`
   - Password: Set via `arcadium_pass` environment variable
   - Test database: `arcadium_testing_wiki` (will be created automatically if missing)

2. **Python environment:**
   - Python 3.11+
   - Virtual environment activated

### Steps

1. **Install dependencies:**
   ```bash
   # From project root
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Ensure test database exists:**
   ```sql
   -- Connect to PostgreSQL as postgres user
   CREATE DATABASE wiki_test;
   ```

   Or let the test setup create it automatically (see `services/wiki/tests/conftest.py`).

3. **Run tests with CI environment variables:**

   **Windows (PowerShell):**
   ```powershell
   $env:FLASK_ENV = "testing"
   # TEST_DATABASE_URL will be constructed from arcadium_user and arcadium_pass if not set
   # Or set explicitly:
   $env:TEST_DATABASE_URL = "postgresql://$env:arcadium_user:$env:arcadium_pass@localhost:5432/arcadium_testing_wiki"
   cd services/wiki
   pytest
   ```

   **Linux/Mac (Bash):**
   ```bash
   export FLASK_ENV=testing
   # TEST_DATABASE_URL will be constructed from arcadium_user and arcadium_pass if not set
   # Or set explicitly:
   export TEST_DATABASE_URL="postgresql://${arcadium_user}:${arcadium_pass}@localhost:5432/wiki_test"
   cd services/wiki
   pytest
   ```

### Quick Test Script

You can create a simple script to run tests like CI:

**`scripts/test-ci-local.sh` (Linux/Mac):**
```bash
#!/bin/bash
export FLASK_ENV=testing
# TEST_DATABASE_URL will be constructed from arcadium_user and arcadium_pass if not set
# Or set explicitly: export TEST_DATABASE_URL="postgresql://${arcadium_user}:${arcadium_pass}@localhost:5432/arcadium_testing_wiki"
cd services/wiki
pytest "$@"
```

**`scripts/test-ci-local.ps1` (Windows PowerShell):**
```powershell
$env:FLASK_ENV = "testing"
# TEST_DATABASE_URL will be constructed from arcadium_user and arcadium_pass if not set
# Or set explicitly: $env:TEST_DATABASE_URL = "postgresql://$env:arcadium_user:$env:arcadium_pass@localhost:5432/wiki_test"
Set-Location services/wiki
pytest $args
```

## Viewing CI Results

### GitHub Actions Dashboard

1. Go to your repository on GitHub
2. Click the **"Actions"** tab
3. Select the **"Wiki Service - Tests"** workflow
4. View individual run results

### Workflow Status Badge

You can add a status badge to your README:

```markdown
![CI Tests](https://github.com/USERNAME/REPO/workflows/Wiki%20Service%20-%20Tests/badge.svg)
```

Replace `USERNAME` and `REPO` with your GitHub username and repository name.

## Troubleshooting

### Tests Fail in CI but Pass Locally

1. **Check database configuration:**
   - Ensure you're using PostgreSQL (not SQLite)
   - Verify `TEST_DATABASE_URL` matches CI exactly
   - Check PostgreSQL version (CI uses PostgreSQL 14)

2. **Check Python version:**
   - CI uses Python 3.11
   - Ensure your local Python version matches

3. **Check dependencies:**
   - Ensure all dependencies from `requirements.txt` are installed
   - Check for version mismatches

4. **Check environment variables:**
   - Verify `FLASK_ENV=testing` is set
   - Verify `TEST_DATABASE_URL` is set correctly

### PostgreSQL Connection Issues in CI

If tests fail with PostgreSQL connection errors:

1. **Check service container:**
   - Verify PostgreSQL service is defined in workflow
   - Check health check configuration
   - Ensure port 5432 is exposed

2. **Check database creation:**
   - Verify `arcadium_testing_wiki` database is created
   - Check PostgreSQL logs in CI output

3. **Check credentials:**
   - Ensure `TEST_DATABASE_URL` uses correct credentials
   - Verify password matches service container configuration

### Slow CI Runs

1. **Check cache:**
   - Verify pip cache is working (look for "Cache restored" in logs)
   - Cache key should include requirements file hashes

2. **Optimize tests:**
   - Consider parallel test execution (`pytest -n auto`)
   - Review slow tests and optimize if needed

## Future Enhancements

### Planned CI/CD Features

- [x] **Multi-service testing:**
  - ✅ Wiki Service tests (backend)
  - ✅ Client tests (frontend)
  - [ ] Game Server tests (when implemented)

- [x] **Code quality checks:**
  - ✅ Linting (ruff)
  - ✅ Code formatting (black, isort)
  - ✅ Pre-commit hooks (trailing whitespace, merge conflicts, YAML/JSON validation)
  - [ ] Type checking (mypy) - Optional future enhancement

- [ ] **Coverage reporting:**
  - Upload coverage reports to Codecov or similar
  - Enforce minimum coverage thresholds
  - Coverage badges in README

- [ ] **Security scanning:**
  - Dependency vulnerability scanning
  - Code security analysis

- [ ] **Build and deployment:**
  - Docker image builds
  - Automated deployment to staging/production
  - Release automation

- [ ] **Performance testing:**
  - Load testing for API endpoints
  - Performance regression detection

## Workflow File Structure

```
.github/
└── workflows/
    ├── wiki-service-tests.yml    # Wiki Service (backend) test workflow
    └── client-tests.yml         # Client (frontend) test workflow
```

## Related Documentation

- [Wiki Service Testing](services/wiki/README.md#testing)
- [Database Configuration](architecture/database-configuration.md)
- [Wiki Implementation Guide](wiki-implementation-guide.md)

## Contributing

When adding new services or features:

1. **Update CI workflows** if needed
2. **Document test requirements** in service README
3. **Ensure tests pass locally** before pushing
4. **Check CI results** after pushing

## Support

If you encounter issues with CI:

1. Check the troubleshooting section above
2. Review GitHub Actions logs for detailed error messages
3. Verify your local environment matches CI configuration
4. Open an issue with:
   - Workflow run link
   - Error messages
   - Steps to reproduce

# CI/CD Documentation

This document describes the Continuous Integration and Continuous Deployment setup for the Arcadium project.

## Overview

The project uses **GitHub Actions** for CI/CD. Currently, CI is configured for the Wiki Service, with plans to expand to other services as they are developed.

## GitHub Actions Workflows

### Wiki Service Tests

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
   - Creates `wiki_test` database
   - Waits for PostgreSQL to be ready

4. **Runs tests:**
   - Executes `pytest` from `services/wiki` directory
   - Uses PostgreSQL test database (avoids SQLite UUID issues)
   - Generates coverage reports

#### Environment Variables

The workflow sets:
- `FLASK_ENV=testing`
- `TEST_DATABASE_URL=postgresql://postgres:Le555ecure@localhost:5432/wiki_test`

#### Test Configuration

Tests use PostgreSQL (not SQLite) to:
- Avoid UUID compatibility issues
- Match production database behavior
- Ensure accurate test results

See `services/wiki/tests/conftest.py` for test database configuration.

## Running CI Tests Locally

To verify tests will pass in CI before pushing, replicate the CI environment locally:

### Prerequisites

1. **PostgreSQL running locally:**
   - Host: `localhost`
   - Port: `5432`
   - User: `postgres`
   - Password: `Le555ecure`
   - Test database: `wiki_test` (will be created automatically if missing)

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
   $env:TEST_DATABASE_URL = "postgresql://postgres:Le555ecure@localhost:5432/wiki_test"
   cd services/wiki
   pytest
   ```
   
   **Linux/Mac (Bash):**
   ```bash
   export FLASK_ENV=testing
   export TEST_DATABASE_URL="postgresql://postgres:Le555ecure@localhost:5432/wiki_test"
   cd services/wiki
   pytest
   ```

### Quick Test Script

You can create a simple script to run tests like CI:

**`scripts/test-ci-local.sh` (Linux/Mac):**
```bash
#!/bin/bash
export FLASK_ENV=testing
export TEST_DATABASE_URL="postgresql://postgres:Le555ecure@localhost:5432/wiki_test"
cd services/wiki
pytest "$@"
```

**`scripts/test-ci-local.ps1` (Windows PowerShell):**
```powershell
$env:FLASK_ENV = "testing"
$env:TEST_DATABASE_URL = "postgresql://postgres:Le555ecure@localhost:5432/wiki_test"
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
   - Verify `wiki_test` database is created
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

- [ ] **Multi-service testing:**
  - Add CI workflows for other services (Game Server, Web Client)
  - Run all service tests in parallel

- [ ] **Code quality checks:**
  - Linting (flake8, pylint, or ruff)
  - Type checking (mypy)
  - Code formatting (black)

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
    └── wiki-service-tests.yml    # Wiki Service test workflow
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

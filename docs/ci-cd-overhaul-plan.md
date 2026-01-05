# CI/CD Overhaul Plan

## Current State Analysis

### Existing Workflows

1. **Wiki Service Tests** (`.github/workflows/wiki-service-tests.yml`)
   - ✅ Uses PostgreSQL correctly
   - ❌ Only tests Wiki service (missing Auth and Shared)
   - ❌ Doesn't use our new test categorization
   - ❌ Doesn't use unified test runner
   - ❌ Only creates `arcadium_testing_wiki` database

2. **Client Tests** (`.github/workflows/client-tests.yml`)
   - ✅ Well organized with parallel jobs
   - ✅ Good test grouping
   - ✅ Proper artifact handling

### Issues Identified

1. **Incomplete Backend Testing**
   - Wiki service only - missing Auth and Shared services
   - No unified backend test workflow

2. **Not Using New Infrastructure**
   - Doesn't use `scripts/run-tests.py all`
   - Doesn't show Wiki test category breakdown
   - Doesn't leverage our new logging system

3. **Database Setup**
   - Only creates Wiki test database
   - Missing Auth test database (`arcadium_testing_auth`)

4. **Organization**
   - Could be better structured
   - Some redundant steps

## Proposed Solution

### New Unified Backend Test Workflow

Create `.github/workflows/backend-tests.yml` that:
- Uses `scripts/run-tests.py all` to run all backend tests
- Shows Wiki test category breakdown
- Creates both test databases (Wiki and Auth)
- Uses our unified logging system
- Provides clear category-level results

### Updated Structure

```
.github/workflows/
├── backend-tests.yml      # Unified backend tests (Wiki, Auth, Shared)
├── client-tests.yml       # Frontend tests (keep as-is, already good)
└── wiki-service-tests.yml # DEPRECATED - can be removed after migration
```

## Implementation Steps

1. Create unified backend test workflow
2. Update database setup to create both databases
3. Use our new test runner with categories
4. Update documentation
5. Optionally deprecate old Wiki-only workflow

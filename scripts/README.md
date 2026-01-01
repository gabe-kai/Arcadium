# Scripts Directory

This directory contains utility scripts for the Arcadium project.

## Test Scripts

### Wiki Service Tests
Run the full Wiki Service test suite manually:

**Using Python (recommended):**
```bash
python scripts/run-wiki-tests.py
```

**Using Bash:**
```bash
bash scripts/run-wiki-tests.sh
```

Both scripts run the same test suite. The Python version is recommended as it's more portable across platforms.

## Hook Installation

### Pre-commit Hooks (Formatting & Linting)
The pre-commit hooks for formatting and linting are managed by the `pre-commit` framework.
To install/update:
```bash
pre-commit install
```

These hooks run automatically on `git commit` and include:
- Trailing whitespace removal
- End of file fixes
- Mixed line ending fixes
- YAML/JSON/TOML validation
- Ruff linting
- Black code formatting
- isort import sorting

**Note:** Test execution has been removed from automatic hooks. Run tests manually before committing/pushing.

### Pre-push Hook (Currently Disabled)
The pre-push hook for running tests is available but not automatically installed.
To install it (if needed):
```bash
bash scripts/install-pre-push-hook.sh
```

**Note:** The pre-push hook is currently disabled. Tests should be run manually before pushing.

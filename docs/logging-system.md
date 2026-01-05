# Arcadium Project - Unified Logging System

## Overview

The Arcadium project uses a **unified logging system** with automatic rotation, size limits, and cleanup. All logs are written to files in the `logs/` directory, organized by type and service.

## Important: Check Log Files, Not Terminal Output

**⚠️ Always check log files for complete test results and service logs.** Terminal output may be truncated or lost. Log files contain the complete, searchable record of all operations.

## Log Directory Structure

```
logs/
├── tests/              # Test run logs
│   ├── test_wiki_*.log
│   ├── test_auth_*.log
│   └── test_all_*.log
├── wiki/               # Wiki service logs
│   └── wiki.log
├── auth/               # Auth service logs
│   └── auth.log
└── README.md           # Log management guide
```

## Log Rotation and Limits

### Test Logs (`logs/tests/`)

- **Max file size**: 50 MB per file
- **Backup count**: 10 files (keeps 10 rotated backups)
- **Rotation**: Size-based (rotates when file reaches 50 MB)
- **Retention**:
  - Age limit: 30 days
  - Total size limit: 1 GB
  - Oldest logs are automatically deleted when limits are exceeded

### Service Logs (`logs/wiki/`, `logs/auth/`)

- **Max file size**: 10 MB per file
- **Backup count**: 5 files
- **Rotation**: Daily at midnight (time-based)
- **Retention**: 30 days or until total size exceeds limits

## Finding and Viewing Logs

### Test Logs

**Latest test summary log:**
```bash
# Linux/Mac
ls -t logs/tests/test_all_*.log | head -1

# Windows PowerShell
Get-ChildItem logs\tests\test_all_*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1
```

**View latest log:**
```bash
# Linux/Mac
cat $(ls -t logs/tests/test_all_*.log | head -1)

# Windows PowerShell
Get-Content (Get-ChildItem logs\tests\test_all_*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
```

**Search for failures:**
```bash
# Linux/Mac
grep -i "FAILED\|ERROR\|FAIL" $(ls -t logs/tests/test_all_*.log | head -1)

# Windows PowerShell
Select-String -Path (Get-ChildItem logs\tests\test_all_*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName -Pattern "FAILED|ERROR|FAIL"
```

### Service Logs

**View Wiki service logs:**
```bash
# Latest log file
tail -f logs/wiki/wiki.log

# Search for errors
grep -i "ERROR" logs/wiki/wiki.log
```

**View Auth service logs:**
```bash
# Latest log file
tail -f logs/auth/auth.log

# Search for errors
grep -i "ERROR" logs/auth/auth.log
```

## Log File Naming

### Test Logs

- Format: `test_<service>_YYYYMMDD_HHMMSS.log`
- Examples:
  - `test_wiki_20250115_143022.log`
  - `test_auth_20250115_143045.log`
  - `test_all_20250115_143000.log`

### Service Logs

- Format: `<service>.log` (with rotated backups: `<service>.log.1`, `<service>.log.2`, etc.)
- Examples:
  - `wiki.log` (current)
  - `wiki.log.20250115` (rotated daily)
  - `auth.log` (current)
  - `auth.log.20250115` (rotated daily)

## Log Format

All logs use a consistent format:

```
YYYY-MM-DD HH:MM:SS [LEVEL    ] logger_name:line_number - message
```

Example:
```
2025-01-15 14:30:22 [INFO    ] app.services.page_service:45 - Page created successfully
2025-01-15 14:30:23 [ERROR   ] app.routes.page_routes:123 - Failed to create page
```

## Automatic Cleanup

The logging system automatically cleans up old logs:

1. **On test run**: Old test logs are cleaned up before new tests run
2. **By age**: Logs older than 30 days are deleted
3. **By size**: If total log size exceeds limits, oldest logs are deleted first

## Configuration

Logging configuration is centralized in `shared/utils/logging_config.py`. Default settings:

- **Test logs**: 50 MB max, 10 backups, 30-day retention, 1 GB total limit
- **Service logs**: 10 MB max, 5 backups, daily rotation, 30-day retention

To customize, modify the defaults in `shared/utils/logging_config.py` or pass parameters when setting up loggers.

## Using the Logging System

### In Test Scripts

Test logs are automatically created by `scripts/run-tests.py`. No additional setup needed.

### In Services

```python
from shared.utils.logging_config import setup_service_logger

# Set up logger for your service
logger = setup_service_logger("wiki")

# Use the logger
logger.info("Service started")
logger.error("An error occurred")
```

### Manual Cleanup

```python
from shared.utils.logging_config import cleanup_old_logs, get_log_dir

# Clean up test logs older than 30 days
logs_dir = get_log_dir() / "tests"
deleted = cleanup_old_logs(logs_dir, max_age_days=30)
print(f"Deleted {deleted} old log files")
```

## Best Practices

1. **Always check log files** - Don't rely solely on terminal output
2. **Search logs for errors** - Use grep/Select-String to find issues
3. **Monitor log sizes** - Check `logs/` directory size periodically
4. **Archive important logs** - Before major changes, archive logs you want to keep
5. **Use log rotation** - Let the system handle rotation automatically

## Troubleshooting

### Logs Not Being Created

1. Check that `logs/` directory exists and is writable
2. Verify Python has write permissions
3. Check for disk space issues

### Logs Growing Too Large

1. Automatic cleanup should handle this
2. Manually run cleanup if needed
3. Adjust retention settings if necessary

### Can't Find Logs

1. Check `logs/` directory in project root
2. Look for subdirectories: `logs/tests/`, `logs/wiki/`, `logs/auth/`
3. Use file search: `find logs -name "*.log"` (Linux/Mac) or `Get-ChildItem logs -Recurse -Filter "*.log"` (Windows)

## Related Documentation

- `logs/README.md` - Detailed log management guide
- `docs/testing-quick-reference.md` - Quick reference for test logs
- `shared/utils/logging_config.py` - Logging configuration source code

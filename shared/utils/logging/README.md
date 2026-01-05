# Unified Logging System

This directory contains the unified logging configuration for the Arcadium project.

## Overview

The Arcadium project uses a centralized logging system with:
- **Automatic file rotation** (size-based and time-based)
- **Size and time limits** with automatic cleanup
- **Consistent formatting** across all services
- **Organized log directories** by service and type

## Configuration

The main logging configuration is in `../logging_config.py` (one level up).

## Features

### Log Rotation

- **Size-based rotation**: Logs rotate when they reach a maximum size
- **Time-based rotation**: Service logs rotate daily at midnight
- **Automatic backups**: Old log files are kept as numbered backups

### Size Limits

- **Test logs**: 50 MB per file, 10 backups (up to 500 MB total)
- **Service logs**: 10 MB per file, 5 backups (up to 50 MB total)

### Time Limits

- **Retention**: Logs are kept for 30 days
- **Automatic cleanup**: Old logs are automatically deleted
- **Total size limit**: Test logs limited to 1 GB total

## Usage

See `docs/logging-system.md` for complete documentation on using the logging system.

## Integration

The logging system is automatically used by:
- Test runner (`scripts/run-tests.py`)
- Services (when configured to use `setup_service_logger`)

## Related Files

- `../logging_config.py` - Main logging configuration
- `../../docs/logging-system.md` - Complete documentation
- `../../logs/README.md` - Log directory guide

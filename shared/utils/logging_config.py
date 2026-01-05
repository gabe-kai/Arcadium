"""
Unified logging configuration for Arcadium project.

This module provides a centralized logging system with:
- File rotation based on size and time
- Consistent log formatting
- Configurable log levels
- Automatic log cleanup
"""

import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Optional

# Default log configuration
DEFAULT_LOG_DIR = Path("logs")
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB per file
DEFAULT_BACKUP_COUNT = 5  # Keep 5 backup files
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_WHEN = "midnight"  # Rotate at midnight
DEFAULT_INTERVAL = 1  # Daily rotation


def get_log_dir(base_path: Optional[Path] = None) -> Path:
    """
    Get the log directory path.

    Args:
        base_path: Base path for logs (defaults to project root)

    Returns:
        Path to log directory
    """
    if base_path is None:
        # Try to find project root by looking for common markers
        current = Path(__file__).resolve()
        while current != current.parent:
            if (current / "requirements.txt").exists() or (current / ".git").exists():
                return current / DEFAULT_LOG_DIR
            current = current.parent
        # Fallback to current directory
        return Path.cwd() / DEFAULT_LOG_DIR
    return base_path / DEFAULT_LOG_DIR


def setup_file_logger(
    name: str,
    log_dir: Optional[Path] = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
    level: int = DEFAULT_LOG_LEVEL,
    use_timed_rotation: bool = False,
    when: str = DEFAULT_WHEN,
    interval: int = DEFAULT_INTERVAL,
) -> logging.Logger:
    """
    Set up a file logger with rotation.

    Args:
        name: Logger name (also used as log file name)
        log_dir: Directory for log files (defaults to logs/ in project root)
        max_bytes: Maximum size per log file (for size-based rotation)
        backup_count: Number of backup files to keep
        level: Logging level
        use_timed_rotation: Use time-based rotation instead of size-based
        when: Time rotation interval ('midnight', 'H', 'D', etc.)
        interval: Number of intervals between rotations

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Don't add handlers if logger already has them
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Create log directory if it doesn't exist
    if log_dir is None:
        log_dir = get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create log file path
    log_file = log_dir / f"{name}.log"

    # Choose rotation handler
    if use_timed_rotation:
        handler = TimedRotatingFileHandler(
            str(log_file),
            when=when,
            interval=interval,
            backupCount=backup_count,
            encoding="utf-8",
        )
        handler.suffix = "%Y%m%d"  # Date suffix for rotated files
    else:
        handler = RotatingFileHandler(
            str(log_file),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )

    # Set formatter
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)8s] %(name)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


def setup_test_logger(
    test_name: str,
    log_dir: Optional[Path] = None,
    max_bytes: int = 50 * 1024 * 1024,  # 50 MB for test logs
    backup_count: int = 10,  # Keep more test logs
) -> logging.Logger:
    """
    Set up a logger specifically for test runs.

    Args:
        test_name: Test name (e.g., 'wiki', 'auth', 'all')
        log_dir: Directory for test logs (defaults to logs/tests/)
        max_bytes: Maximum size per test log file
        backup_count: Number of backup files to keep

    Returns:
        Configured logger instance
    """
    if log_dir is None:
        base_log_dir = get_log_dir()
        log_dir = base_log_dir / "tests"

    return setup_file_logger(
        f"test_{test_name}",
        log_dir=log_dir,
        max_bytes=max_bytes,
        backup_count=backup_count,
        level=logging.DEBUG,  # More verbose for tests
    )


def setup_service_logger(
    service_name: str,
    log_dir: Optional[Path] = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
    use_timed_rotation: bool = True,  # Services use daily rotation
) -> logging.Logger:
    """
    Set up a logger for a service (wiki, auth, etc.).

    Args:
        service_name: Service name (e.g., 'wiki', 'auth')
        log_dir: Directory for service logs (defaults to logs/<service>/)
        max_bytes: Maximum size per log file
        backup_count: Number of backup files to keep
        use_timed_rotation: Use daily rotation

    Returns:
        Configured logger instance
    """
    if log_dir is None:
        base_log_dir = get_log_dir()
        log_dir = base_log_dir / service_name

    return setup_file_logger(
        service_name,
        log_dir=log_dir,
        max_bytes=max_bytes,
        backup_count=backup_count,
        use_timed_rotation=use_timed_rotation,
        level=logging.INFO,
    )


def cleanup_old_logs(
    log_dir: Path,
    max_age_days: int = 30,
    max_total_size_mb: Optional[int] = None,
) -> int:
    """
    Clean up old log files.

    Args:
        log_dir: Directory containing log files
        max_age_days: Delete logs older than this many days
        max_total_size_mb: If set, delete oldest logs until total size is under this limit

    Returns:
        Number of files deleted
    """
    import time

    if not log_dir.exists():
        return 0

    deleted_count = 0
    cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)

    # Get all log files
    log_files = list(log_dir.glob("*.log*"))

    # Delete by age
    for log_file in log_files:
        if log_file.stat().st_mtime < cutoff_time:
            try:
                log_file.unlink()
                deleted_count += 1
            except Exception:
                pass

    # Delete by total size if specified
    if max_total_size_mb:
        max_total_bytes = max_total_size_mb * 1024 * 1024
        log_files = sorted(
            [f for f in log_dir.glob("*.log*") if f.exists()],
            key=lambda f: f.stat().st_mtime,
        )

        total_size = sum(f.stat().st_size for f in log_files)

        while total_size > max_total_bytes and log_files:
            oldest = log_files.pop(0)
            try:
                size = oldest.stat().st_size
                oldest.unlink()
                total_size -= size
                deleted_count += 1
            except Exception:
                pass

    return deleted_count

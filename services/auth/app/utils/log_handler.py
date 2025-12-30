"""
In-memory log handler for capturing recent log entries.
Used to expose logs via API endpoints.
"""

import logging
from collections import deque
from datetime import datetime
from typing import Dict, List


class InMemoryLogHandler(logging.Handler):
    """Log handler that stores recent log entries in memory."""

    def __init__(self, max_entries: int = 1000):
        """
        Initialize the in-memory log handler.

        Args:
            max_entries: Maximum number of log entries to keep in memory
        """
        super().__init__()
        self.logs = deque(maxlen=max_entries)
        self.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    def emit(self, record):
        """Store log record in memory."""
        try:
            formatted = self.format(record)
            self.logs.append(
                {
                    "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": formatted,
                    "raw_message": record.getMessage(),
                }
            )
        except Exception:
            # Ignore errors in log handler to prevent infinite loops
            pass

    def get_recent_logs(self, limit: int = 100, level: str = None) -> List[Dict]:
        """
        Get recent log entries.

        Args:
            limit: Maximum number of entries to return
            level: Filter by log level (e.g., 'ERROR', 'WARNING', 'INFO')

        Returns:
            List of log entries, most recent first
        """
        logs = list(self.logs)

        # Filter by level if specified
        if level:
            logs = [log for log in logs if log["level"] == level]

        # Return most recent first, limited to requested count
        return list(reversed(logs[-limit:]))


# Global log handler instance
_log_handler = None


def get_log_handler() -> InMemoryLogHandler:
    """Get or create the global in-memory log handler."""
    global _log_handler
    if _log_handler is None:
        _log_handler = InMemoryLogHandler(max_entries=1000)
        # Add to root logger to capture all logs
        root_logger = logging.getLogger()
        root_logger.addHandler(_log_handler)
        # Also add to Flask app logger
        logging.getLogger("flask").addHandler(_log_handler)
    return _log_handler

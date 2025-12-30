"""Tests for in-memory log handler"""

import logging

import pytest
from app.utils.log_handler import InMemoryLogHandler, get_log_handler


def test_in_memory_log_handler_initialization():
    """Test that log handler initializes correctly"""
    handler = InMemoryLogHandler(max_entries=100)
    assert handler.max_entries == 100
    assert len(handler.logs) == 0


def test_in_memory_log_handler_emit():
    """Test that log handler captures log records"""
    handler = InMemoryLogHandler(max_entries=100)
    logger = logging.getLogger("test_logger")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    logger.info("Test info message")
    logger.error("Test error message")

    assert len(handler.logs) == 2
    assert handler.logs[0]["level"] == "INFO"
    assert handler.logs[1]["level"] == "ERROR"
    assert "Test info message" in handler.logs[0]["message"]
    assert "Test error message" in handler.logs[1]["message"]


def test_in_memory_log_handler_get_logs():
    """Test getting recent logs"""
    handler = InMemoryLogHandler(max_entries=100)
    logger = logging.getLogger("test_logger")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    logger.info("Message 1")
    logger.warning("Message 2")
    logger.error("Message 3")

    logs = handler.get_recent_logs(limit=2)
    assert len(logs) == 2
    # Should return most recent first
    assert logs[0]["level"] == "ERROR"
    assert logs[1]["level"] == "WARNING"


def test_in_memory_log_handler_get_logs_with_level_filter():
    """Test filtering logs by level"""
    handler = InMemoryLogHandler(max_entries=100)
    logger = logging.getLogger("test_logger")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.info("Another info message")

    error_logs = handler.get_recent_logs(limit=100, level="ERROR")
    assert len(error_logs) == 1
    assert error_logs[0]["level"] == "ERROR"

    info_logs = handler.get_recent_logs(limit=100, level="INFO")
    assert len(info_logs) == 2
    assert all(log["level"] == "INFO" for log in info_logs)


def test_in_memory_log_handler_max_entries():
    """Test that log handler respects max_entries limit"""
    handler = InMemoryLogHandler(max_entries=5)
    logger = logging.getLogger("test_logger")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    # Log more than max_entries
    for i in range(10):
        logger.info(f"Message {i}")

    # Should only keep the most recent max_entries
    assert len(handler.logs) == 5
    # Should have the last 5 messages
    assert "Message 9" in handler.logs[-1]["message"]
    assert "Message 5" in handler.logs[0]["message"]


def test_in_memory_log_handler_log_format():
    """Test that log entries include all required fields"""
    handler = InMemoryLogHandler(max_entries=100)
    logger = logging.getLogger("test_logger")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    logger.info("Test message")

    assert len(handler.logs) == 1
    log_entry = handler.logs[0]
    assert "timestamp" in log_entry
    assert "level" in log_entry
    assert "message" in log_entry
    assert "raw_message" in log_entry
    assert "pathname" in log_entry
    assert "lineno" in log_entry
    assert "funcName" in log_entry
    assert "process" in log_entry
    assert "thread" in log_entry
    assert "threadName" in log_entry


def test_get_log_handler_singleton():
    """Test that get_log_handler returns singleton"""
    handler1 = get_log_handler()
    handler2 = get_log_handler()

    assert handler1 is handler2


def test_get_log_handler_attaches_to_loggers():
    """Test that get_log_handler attaches to root and Flask loggers"""
    handler = get_log_handler()

    root_logger = logging.getLogger()
    flask_logger = logging.getLogger("flask")

    assert handler in root_logger.handlers
    assert handler in flask_logger.handlers


def test_in_memory_log_handler_handles_emit_errors():
    """Test that log handler handles errors gracefully during emit"""
    handler = InMemoryLogHandler(max_entries=100)
    # Create a record that will cause an error
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Test",
        args=(),
        exc_info=None,
    )
    # Mock format to raise an error
    handler.format = lambda r: exec("raise Exception('Format error')")

    # Should not raise, just ignore the error
    try:
        handler.emit(record)
    except Exception:
        pytest.fail("Handler should not raise exceptions during emit")

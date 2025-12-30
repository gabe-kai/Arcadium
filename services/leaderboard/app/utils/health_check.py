"""
Standard health check utility for Arcadium services.

This module provides a standardized health check function that all services
should use to ensure consistent health endpoint responses with process metadata.
"""

import os
import platform
import time
from typing import Dict, Optional

# Try to import psutil, but make it optional
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None


def get_health_status(
    service_name: str,
    version: str = "1.0.0",
    additional_info: Optional[Dict] = None,
    include_process_info: bool = True,
) -> Dict:
    """
    Generate a standardized health check response.

    Args:
        service_name: Name of the service (e.g., "wiki", "auth")
        version: Service version (default: "1.0.0")
        additional_info: Optional dictionary with additional service-specific info
        include_process_info: Whether to include process information (default: True)

    Returns:
        Dictionary with health status information:
        {
            "status": "healthy",
            "service": service_name,
            "version": version,
            "process_info": {
                "pid": int,
                "uptime_seconds": float,
                "cpu_percent": float,
                "memory_mb": float,
                "memory_percent": float,
                "threads": int,
                "open_files": int (0 on Windows)
            },
            ...additional_info
        }
    """
    health_status = {
        "status": "healthy",
        "service": service_name,
        "version": version,
    }

    # Add process information if requested and psutil is available
    if include_process_info and PSUTIL_AVAILABLE:
        try:
            process = psutil.Process()
            # Use oneshot() for efficiency
            with process.oneshot():
                create_time = process.create_time()
                uptime_seconds = time.time() - create_time
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)

                # Get CPU percent (non-blocking)
                try:
                    cpu_percent = process.cpu_percent(interval=None)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    cpu_percent = 0.0

                # Get memory percent
                try:
                    memory_percent = process.memory_percent()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    memory_percent = 0.0

                # Get thread count
                try:
                    threads = process.num_threads()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    threads = 0

                # Skip open_files() on Windows - it's extremely slow
                if platform.system() == "Windows":
                    open_files = 0
                else:
                    try:
                        open_files = len(process.open_files())
                    except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
                        open_files = 0

            health_status["process_info"] = {
                "pid": process.pid,
                "uptime_seconds": round(uptime_seconds, 2),
                "cpu_percent": round(cpu_percent, 2),
                "memory_mb": round(memory_mb, 2),
                "memory_percent": round(memory_percent, 2),
                "threads": threads,
                "open_files": open_files,
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
            # Fallback if psutil fails
            health_status["process_info"] = {
                "pid": os.getpid(),
                "uptime_seconds": 0.0,
                "cpu_percent": 0.0,
                "memory_mb": 0.0,
                "memory_percent": 0.0,
                "threads": 0,
                "open_files": 0,
            }
    elif include_process_info:
        # Basic info without psutil
        health_status["process_info"] = {
            "pid": os.getpid(),
            "uptime_seconds": 0.0,
            "cpu_percent": 0.0,
            "memory_mb": 0.0,
            "memory_percent": 0.0,
            "threads": 0,
            "open_files": 0,
            "note": "psutil not available",
        }

    # Add any additional service-specific information
    if additional_info:
        health_status.update(additional_info)

    return health_status

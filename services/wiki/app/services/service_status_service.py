"""
Service status monitoring service.

Checks health of all Arcadium services and manages the service status page.
"""

import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

import requests
from app import db
from app.models.page import Page
from app.models.wiki_config import WikiConfig

# Try to import psutil, but make it optional
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None


class ServiceStatusService:
    """Service for monitoring and managing service status"""

    # Shared requests session for connection pooling (improves performance)
    _session = None

    # Service definitions
    SERVICES = {
        "wiki": {
            "name": "Wiki Service",
            "description": "Core wiki service providing page management, search, navigation, and content APIs",
            "url": os.getenv("WIKI_SERVICE_URL", "http://localhost:5000"),
            "health_endpoint": "/api/health",
            "logs_endpoint": "/api/admin/logs",  # Logs endpoint
        },
        "auth": {
            "name": "Auth Service",
            "description": "Authentication and user management service handling login, registration, and JWT tokens",
            "url": os.getenv("AUTH_SERVICE_URL", "http://localhost:8000"),
            "health_endpoint": "/health",  # Auth service has /health at root
            "logs_endpoint": "/api/logs",  # Logs endpoint
        },
        "file-watcher": {
            "name": "File Watcher Service",
            "description": "AI Content Management file watcher that monitors markdown files and syncs changes to the database",
            "url": os.getenv(
                "WIKI_SERVICE_URL", "http://localhost:5000"
            ),  # Runs as part of wiki service
            "health_endpoint": "/api/health",  # Uses wiki service health endpoint
            "is_internal": True,  # Flag to indicate it's not a separate HTTP service
        },
        "notification": {
            "name": "Notification Service",
            "description": "Handles user notifications and alerts across the platform",
            "url": os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8006"),
            "health_endpoint": "/health",
        },
        "game-server": {
            "name": "Game Server",
            "description": "Core game server handling game logic, player sessions, and game state",
            "url": os.getenv("GAME_SERVER_URL", "http://localhost:8080"),
            "health_endpoint": "/health",
        },
        "web-client": {
            "name": "Web Client",
            "description": "Frontend React application providing the user interface for the wiki and platform",
            "url": os.getenv("WEB_CLIENT_URL", "http://localhost:3000"),
            "health_endpoint": "/health",  # Web client now has /health endpoint
        },
        "admin": {
            "name": "Admin Service",
            "description": "Administrative service for platform management and configuration",
            "url": os.getenv("ADMIN_SERVICE_URL", "http://localhost:8001"),
            "health_endpoint": "/health",
        },
        "assets": {
            "name": "Assets Service",
            "description": "Manages static assets, file uploads, and media storage",
            "url": os.getenv("ASSETS_SERVICE_URL", "http://localhost:8002"),
            "health_endpoint": "/health",
        },
        "chat": {
            "name": "Chat Service",
            "description": "Real-time chat and messaging service for user communication",
            "url": os.getenv("CHAT_SERVICE_URL", "http://localhost:8003"),
            "health_endpoint": "/health",
        },
        "leaderboard": {
            "name": "Leaderboard Service",
            "description": "Tracks and displays player rankings, scores, and achievements",
            "url": os.getenv("LEADERBOARD_SERVICE_URL", "http://localhost:8004"),
            "health_endpoint": "/health",
        },
        "presence": {
            "name": "Presence Service",
            "description": "Tracks user online/offline status and active sessions",
            "url": os.getenv("PRESENCE_SERVICE_URL", "http://localhost:8005"),
            "health_endpoint": "/health",
        },
    }

    @staticmethod
    def check_service_health(service_id: str, timeout: float = 2.0) -> Dict:
        """
        Check health of a specific service.

        Args:
            service_id: Service identifier (e.g., 'wiki', 'auth')
            timeout: Request timeout in seconds

        Returns:
            Dictionary with health check results:
            {
                'status': 'healthy' | 'degraded' | 'unhealthy',
                'response_time_ms': float,
                'error': str (if any),
                'details': dict (from health endpoint)
            }
        """
        if service_id not in ServiceStatusService.SERVICES:
            return {
                "status": "unhealthy",
                "response_time_ms": 0,
                "error": f"Unknown service: {service_id}",
                "details": {},
            }

        service = ServiceStatusService.SERVICES[service_id]

        # For internal services like file-watcher, check if the parent service is healthy
        # and indicate it's an internal component
        if service.get("is_internal", False):
            # Check the parent service (wiki service in this case)
            parent_result = ServiceStatusService.check_service_health(
                "wiki", timeout=timeout
            )
            # Mark as internal component - status depends on parent
            parent_result["is_internal"] = True
            parent_result["note"] = (
                "Internal component - status reflects parent service"
            )

            # Try to detect if file watcher is running as a separate process
            if service_id == "file-watcher":
                watcher_info = ServiceStatusService.get_file_watcher_info()
                if watcher_info:
                    parent_result["process_info"] = watcher_info.get("process_info")
                    parent_result["watcher_metadata"] = watcher_info.get("metadata", {})
                    parent_result["is_running"] = watcher_info.get("is_running", False)
                else:
                    parent_result["is_running"] = False
                    parent_result["note"] = (
                        "File watcher not detected as separate process (may be running in same process as wiki service)"
                    )

            return parent_result

        url = f"{service['url']}{service['health_endpoint']}"

        # Use a session with connection pooling for better performance
        # Create session if it doesn't exist (module-level, reused across calls)
        if ServiceStatusService._session is None:
            ServiceStatusService._session = requests.Session()
            # Set default timeout for the session
            ServiceStatusService._session.timeout = timeout

        start_time = time.time()
        try:
            response = ServiceStatusService._session.get(url, timeout=timeout)
            response_time_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                # Try to parse JSON, but handle non-JSON responses gracefully
                try:
                    data = response.json()
                    status = data.get("status", "healthy")

                    # Determine status based on response
                    status_reason = None
                    if status == "healthy":
                        # Check response time thresholds
                        # For cross-service health checks on localhost, we expect < 200ms typically
                        # But Windows + psutil + connection setup can add overhead
                        # So we use reasonable thresholds that account for this
                        if response_time_ms > 2000:  # 2 seconds - definitely unhealthy
                            status = "unhealthy"
                            status_reason = f"Slow response time ({response_time_ms:.0f}ms exceeds 2000ms threshold)"
                        elif (
                            response_time_ms > 1500
                        ):  # 1.5 seconds - degraded (slow but functional)
                            status = "degraded"
                            status_reason = f"Slow response time ({response_time_ms:.0f}ms exceeds 1500ms threshold)"
                        # Note: < 1500ms is acceptable for cross-service health checks
                        # due to connection setup, network latency, and process info gathering

                    # Check if the health endpoint itself reported a non-healthy status
                    if status != "healthy" and not status_reason:
                        # The service's own health endpoint reported degraded/unhealthy
                        status_reason = (
                            data.get("reason")
                            or data.get("message")
                            or "Service reported non-healthy status"
                        )

                    return {
                        "status": status,
                        "response_time_ms": round(response_time_ms, 2),
                        "error": None,
                        "status_reason": status_reason,  # Add reason for non-healthy status
                        "details": data,
                    }
                except (ValueError, TypeError) as json_error:
                    # Response is not JSON - might be HTML or plain text
                    # If we got a 200, consider it healthy (service is responding)
                    content_type = response.headers.get("content-type", "").lower()
                    if "text/html" in content_type:
                        # HTML response (like from web client) - service is up
                        return {
                            "status": "healthy",
                            "response_time_ms": round(response_time_ms, 2),
                            "error": None,
                            "details": {"note": "Service responding (HTML response)"},
                        }
                    else:
                        # Other non-JSON response
                        return {
                            "status": "degraded",
                            "response_time_ms": round(response_time_ms, 2),
                            "error": f"Non-JSON response: {str(json_error)[:50]}",
                            "status_reason": "Service returned non-JSON response - may be misconfigured",
                            "details": {},
                        }
            elif response.status_code in (401, 403):
                # Auth endpoints might return 401/403 - service is up, just needs auth
                return {
                    "status": "healthy",
                    "response_time_ms": round(response_time_ms, 2),
                    "error": None,
                    "details": {
                        "note": f"Service responding (HTTP {response.status_code})"
                    },
                }
            else:
                return {
                    "status": "unhealthy",
                    "response_time_ms": round((time.time() - start_time) * 1000, 2),
                    "error": f"HTTP {response.status_code}",
                    "status_reason": f"HTTP {response.status_code} error - service may be experiencing issues",
                    "details": {},
                }
        except requests.exceptions.Timeout:
            return {
                "status": "unhealthy",
                "response_time_ms": timeout * 1000,
                "error": "Request timeout",
                "details": {},
            }
        except requests.exceptions.ConnectionError:
            return {
                "status": "unhealthy",
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "error": "Connection refused",
                "details": {},
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "error": str(e),
                "details": {},
            }

    @staticmethod
    def get_current_process_info() -> Dict:
        """
        Get process information for the current Flask process.

        Returns:
            Dictionary with process information:
            {
                'pid': int,
                'uptime_seconds': float,
                'cpu_percent': float,
                'memory_mb': float,
                'memory_percent': float,
                'threads': int,
                'open_files': int,
            }
        """
        # If psutil is not available, return basic info only
        if not PSUTIL_AVAILABLE:
            return {
                "pid": os.getpid(),
                "uptime_seconds": 0.0,
                "cpu_percent": 0.0,
                "memory_mb": 0.0,
                "memory_percent": 0.0,
                "threads": 0,
                "open_files": 0,
                "error": "psutil not available - install with: pip install psutil",
            }

        try:
            process = psutil.Process()
            with process.oneshot():
                # Get process creation time
                create_time = process.create_time()
                uptime_seconds = time.time() - create_time

                # Get memory info
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)  # Convert to MB

                # Get CPU percent (non-blocking, may return 0.0 on first call)
                try:
                    cpu_percent = process.cpu_percent(interval=0.1)
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

                # Get open file descriptors
                try:
                    open_files = len(process.open_files())
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    open_files = 0

            return {
                "pid": process.pid,
                "uptime_seconds": round(uptime_seconds, 2),
                "cpu_percent": round(cpu_percent, 2),
                "memory_mb": round(memory_mb, 2),
                "memory_percent": round(memory_percent, 2),
                "threads": threads,
                "open_files": open_files,
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError) as e:
            # Fallback if psutil fails or process info unavailable
            return {
                "pid": os.getpid(),
                "uptime_seconds": 0.0,
                "cpu_percent": 0.0,
                "memory_mb": 0.0,
                "memory_percent": 0.0,
                "threads": 0,
                "open_files": 0,
                "error": str(e),
            }

    @staticmethod
    def get_file_watcher_info() -> Optional[Dict]:
        """
        Try to detect if the file watcher is running as a separate process.

        Returns:
            Dictionary with process info and metadata if found, None otherwise
        """
        if not PSUTIL_AVAILABLE:
            return None

        try:
            current_pid = os.getpid()

            # Look for Python processes that might be the file watcher
            # Check for processes with "watch" or "file_watcher" in command line
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    proc_info = proc.info
                    # Skip current process
                    if proc_info["pid"] == current_pid:
                        continue

                    cmdline = proc_info.get("cmdline", [])
                    if not cmdline:
                        continue

                    # Check if this looks like the file watcher process
                    cmdline_str = " ".join(cmdline).lower()
                    is_watcher = "python" in cmdline_str and (
                        "app.sync watch" in cmdline_str
                        or "app/sync/watch" in cmdline_str
                        or "file_watcher" in cmdline_str
                        or "sync watch" in cmdline_str
                    )

                    if is_watcher:
                        # Found the file watcher process - get full process object
                        process = psutil.Process(proc_info["pid"])
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

                            # Extract metadata from command line
                            metadata = {
                                "command": " ".join(cmdline),
                                "watched_directory": None,  # Could parse from command line if available
                                "debounce_seconds": 1.0,  # Default, could be parsed from command line
                            }

                            # Try to extract debounce time from command line
                            for i, arg in enumerate(cmdline):
                                if arg in ["--debounce", "-d"] and i + 1 < len(cmdline):
                                    try:
                                        metadata["debounce_seconds"] = float(
                                            cmdline[i + 1]
                                        )
                                    except (ValueError, IndexError):
                                        pass

                            return {
                                "is_running": True,
                                "process_info": {
                                    "pid": process.pid,
                                    "uptime_seconds": round(uptime_seconds, 2),
                                    "cpu_percent": round(cpu_percent, 2),
                                    "memory_mb": round(memory_mb, 2),
                                    "memory_percent": round(memory_percent, 2),
                                    "threads": threads,
                                    "open_files": 0,  # Could be added if needed
                                },
                                "metadata": metadata,
                            }
                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    # Process disappeared or access denied, skip
                    continue
                except Exception:
                    # Other errors, skip
                    continue

            # File watcher not found as separate process
            return None

        except Exception:
            # Error detecting file watcher, return None
            return None

    @staticmethod
    def check_all_services() -> Dict[str, Dict]:
        """
        Check health of all services.
        Uses shorter timeouts to return quickly even if some services are slow.

        Returns:
            Dictionary mapping service_id to health check results
        """
        results = {}

        # Check wiki service first (current process) - use very short timeout since it's local
        if "wiki" in ServiceStatusService.SERVICES:
            try:
                wiki_result = ServiceStatusService.check_service_health(
                    "wiki", timeout=0.5
                )
                # Add process info for the wiki service (current process)
                process_info = ServiceStatusService.get_current_process_info()
                wiki_result["process_info"] = process_info
                results["wiki"] = wiki_result
            except Exception as e:
                # If wiki check fails, still return basic info
                results["wiki"] = {
                    "status": "unhealthy",
                    "response_time_ms": 0,
                    "error": f"Wiki service check failed: {str(e)}",
                    "details": {},
                }
                process_info = ServiceStatusService.get_current_process_info()
                results["wiki"]["process_info"] = process_info

        # Check other services with very short timeout (1 second max per service)
        # This ensures the endpoint returns quickly even if many services are down
        for service_id in ServiceStatusService.SERVICES.keys():
            if service_id != "wiki":  # Already checked above
                try:
                    # Use very short timeout for external services
                    # Internal services will check their parent service
                    # For local services (localhost), use shorter timeout since network latency is minimal
                    service_url = ServiceStatusService.SERVICES[service_id].get(
                        "url", ""
                    )
                    is_local = "localhost" in service_url or "127.0.0.1" in service_url
                    timeout = (
                        0.5 if is_local else 1.0
                    )  # Faster timeout for local services
                    results[service_id] = ServiceStatusService.check_service_health(
                        service_id, timeout=timeout
                    )

                    # Extract process info, version, and service_name from health endpoint responses
                    if "details" in results[service_id] and isinstance(
                        results[service_id]["details"], dict
                    ):
                        details = results[service_id]["details"]
                        if "process_info" in details:
                            results[service_id]["process_info"] = details[
                                "process_info"
                            ]
                        if "version" in details:
                            results[service_id]["version"] = details["version"]
                        if "service_name" in details:
                            results[service_id]["service_name"] = details[
                                "service_name"
                            ]
                except Exception as e:
                    # If any service check fails catastrophically, mark as unhealthy
                    results[service_id] = {
                        "status": "unhealthy",
                        "response_time_ms": 0,
                        "error": f"Check failed: {str(e)}",
                        "details": {},
                    }

        return results

    @staticmethod
    def get_status_indicator(status: str) -> str:
        """
        Get status indicator emoji.

        Args:
            status: 'healthy', 'degraded', or 'unhealthy'

        Returns:
            Emoji indicator
        """
        indicators = {"healthy": "🟢", "degraded": "🟡", "unhealthy": "🔴"}
        return indicators.get(status, "⚪")

    @staticmethod
    def get_status_display_name(status: str) -> str:
        """
        Get display name for status.

        Args:
            status: 'healthy', 'degraded', or 'unhealthy'

        Returns:
            Display name
        """
        names = {"healthy": "Healthy", "degraded": "Degraded", "unhealthy": "Unhealthy"}
        return names.get(status, "Unknown")

    @staticmethod
    def get_service_status_page() -> Optional[Page]:
        """
        Get the service status system page.

        Returns:
            Page object or None if not found
        """
        return (
            db.session.query(Page)
            .filter_by(slug="service-status", is_system_page=True)
            .first()
        )

    @staticmethod
    def create_or_update_status_page(
        user_id: uuid.UUID, status_data: Dict[str, Dict]
    ) -> Page:
        """
        Create or update the service status page with current status data.

        Args:
            user_id: User ID for page creation/update
            status_data: Dictionary of service_id -> health check results

        Returns:
            Page object
        """
        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S UTC")

        # Build markdown content
        content_lines = [
            "# Arcadium Service Status",
            "",
            f"*Last Updated: {timestamp}*",
            "",
            "## Services",
            "",
            "| Service | Status | Last Check | Response Time | Notes |",
            "|---------|--------|------------|---------------|-------|",
        ]

        # Add service rows
        for service_id, service_info in ServiceStatusService.SERVICES.items():
            health = status_data.get(service_id, {})
            status = health.get("status", "unhealthy")
            indicator = ServiceStatusService.get_status_indicator(status)
            status_name = ServiceStatusService.get_status_display_name(status)
            response_time = health.get("response_time_ms", 0)
            response_time_str = f"{response_time}ms" if response_time > 0 else "N/A"
            error = health.get("error")
            notes = error if error else "-"

            content_lines.append(
                f"| {service_info['name']} | {indicator} {status_name} | {timestamp} | {response_time_str} | {notes} |"
            )

        content_lines.extend(
            [
                "",
                "## Status Notes",
                "",
                "*Status checks run automatically. Manual updates can be made by administrators.*",
            ]
        )

        # Add notes for non-healthy services
        has_notes = False
        for service_id, service_info in ServiceStatusService.SERVICES.items():
            health = status_data.get(service_id, {})
            status = health.get("status", "unhealthy")
            if status != "healthy":
                has_notes = True
                indicator = ServiceStatusService.get_status_indicator(status)
                error = health.get("error", "Unknown issue")
                content_lines.append(
                    f"### {service_info['name']} ({indicator} {ServiceStatusService.get_status_display_name(status)})"
                )
                content_lines.append(f"- **Issue**: {error}")
                content_lines.append(f"- **Last Updated**: {timestamp}")
                content_lines.append("")

        if not has_notes:
            content_lines.append("*All services are operating normally.*")

        content = "\n".join(content_lines)

        # Get or create page
        page = ServiceStatusService.get_service_status_page()

        if page:
            # Update existing page
            page.content = content
            page.updated_by = user_id
            page.title = "Arcadium Service Status"
        else:
            # Create new page
            page = Page(
                title="Arcadium Service Status",
                slug="service-status",
                content=content,
                created_by=user_id,
                updated_by=user_id,
                is_system_page=True,
                status="published",
                file_path="service-status.md",
            )
            db.session.add(page)

        db.session.commit()
        return page

    @staticmethod
    def get_manual_status_notes() -> Dict[str, Dict]:
        """
        Get manually set status notes from config.

        Returns:
            Dictionary mapping service_id to note data
        """
        notes = {}
        for service_id in ServiceStatusService.SERVICES.keys():
            config_key = f"service_status_notes_{service_id}"
            config = db.session.query(WikiConfig).filter_by(key=config_key).first()
            if config:
                try:
                    import json

                    notes[service_id] = json.loads(config.value)
                except (json.JSONDecodeError, ValueError):
                    notes[service_id] = {"notes": config.value}
        return notes

    @staticmethod
    def set_manual_status_notes(service_id: str, notes_data: Dict, user_id: uuid.UUID):
        """
        Set manual status notes for a service.

        Args:
            service_id: Service identifier
            notes_data: Dictionary with note fields (issue, impact, eta, etc.)
            user_id: User ID setting the notes
        """
        config_key = f"service_status_notes_{service_id}"
        import json

        config = db.session.query(WikiConfig).filter_by(key=config_key).first()
        if config:
            config.value = json.dumps(notes_data)
            config.updated_by = user_id
        else:
            config = WikiConfig(
                key=config_key, value=json.dumps(notes_data), updated_by=user_id
            )
            db.session.add(config)

        db.session.commit()

    @staticmethod
    def get_service_process_info(service_id: str) -> Optional[Dict]:
        """
        Get process information for a service by finding its running process.

        Args:
            service_id: Service identifier (e.g., 'wiki', 'auth', 'web-client')

        Returns:
            Dictionary with process info if found, None otherwise
        """
        if not PSUTIL_AVAILABLE:
            return None

        service = ServiceStatusService.SERVICES.get(service_id)
        if not service:
            return None

        # Define process search patterns for each service
        # Use flexible matching - check for key identifiers in command line
        search_patterns = {
            "wiki": {
                "required": ["flask", "run"],
                "optional": ["wiki", "5000"],  # Port or service name
            },
            "auth": {
                "required": ["flask", "run"],
                "optional": ["8000", "auth"],  # Port or service name
            },
            "web-client": {
                "required": ["vite", "dev"],
                "optional": ["npm", "3000"],  # npm run dev or port
            },
            "file-watcher": {
                "required": ["app.sync", "watch"],
                "optional": ["python"],
            },
        }

        patterns = search_patterns.get(service_id)
        if not patterns:
            return None

        try:
            current_pid = os.getpid()
            for proc in psutil.process_iter(["pid", "name", "cmdline", "create_time"]):
                try:
                    proc_info = proc.info
                    if proc_info["pid"] == current_pid:
                        continue

                    cmdline = proc_info.get("cmdline", [])
                    if not cmdline:
                        continue

                    cmdline_str = " ".join(cmdline).lower()
                    # Check if process matches service patterns
                    # Must have all required patterns, and at least one optional
                    required_match = all(
                        pattern.lower() in cmdline_str
                        for pattern in patterns["required"]
                    )
                    optional_match = any(
                        pattern.lower() in cmdline_str
                        for pattern in patterns["optional"]
                    )

                    if required_match and optional_match:
                        create_time = proc_info.get("create_time", 0)
                        uptime_seconds = (
                            time.time() - create_time if create_time > 0 else 0
                        )

                        try:
                            memory_info = proc.memory_info()
                            memory_mb = memory_info.rss / (1024 * 1024)
                            cpu_percent = proc.cpu_percent(interval=0.1)
                            memory_percent = proc.memory_percent()
                            threads = proc.num_threads()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            memory_mb = 0
                            cpu_percent = 0
                            memory_percent = 0
                            threads = 0

                        return {
                            "pid": proc_info["pid"],
                            "uptime_seconds": round(uptime_seconds, 2),
                            "cpu_percent": round(cpu_percent, 2),
                            "memory_mb": round(memory_mb, 2),
                            "memory_percent": round(memory_percent, 2),
                            "threads": threads,
                            "command": " ".join(cmdline),
                        }
                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    continue
        except Exception:
            pass

        return None

    @staticmethod
    def stop_service(service_id: str) -> Dict:
        """
        Stop a service by terminating its process.

        Args:
            service_id: Service identifier

        Returns:
            Dictionary with result: {'success': bool, 'message': str}
        """
        if not PSUTIL_AVAILABLE:
            return {
                "success": False,
                "message": "psutil not available - cannot control services",
            }

        process_info = ServiceStatusService.get_service_process_info(service_id)
        if not process_info:
            return {
                "success": False,
                "message": f"Service {service_id} is not running",
            }

        try:
            pid = process_info["pid"]
            proc = psutil.Process(pid)
            proc.terminate()  # Graceful shutdown
            # Wait up to 5 seconds for process to terminate
            try:
                proc.wait(timeout=5)
            except psutil.TimeoutExpired:
                # Force kill if graceful termination failed
                proc.kill()
                proc.wait(timeout=2)

            return {
                "success": True,
                "message": f"Service {service_id} stopped successfully",
                "pid": pid,
            }
        except psutil.NoSuchProcess:
            return {
                "success": False,
                "message": f"Process for {service_id} no longer exists",
            }
        except psutil.AccessDenied:
            return {
                "success": False,
                "message": f"Permission denied - cannot stop {service_id}",
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error stopping {service_id}: {str(e)}",
            }

    @staticmethod
    def start_service(service_id: str) -> Dict:
        """
        Start a service by launching its process.

        Args:
            service_id: Service identifier

        Returns:
            Dictionary with result: {'success': bool, 'message': str, 'pid': int}
        """
        # Check if service is already running
        process_info = ServiceStatusService.get_service_process_info(service_id)
        if process_info:
            return {
                "success": False,
                "message": f"Service {service_id} is already running (PID: {process_info['pid']})",
            }

        # Get project root directory (assume we're in services/wiki)
        project_root = Path(__file__).parent.parent.parent.parent.resolve()

        # Define service start commands
        service_commands = {
            "wiki": {
                "cwd": project_root / "services" / "wiki",
                "command": [sys.executable, "-m", "flask", "run"],
                "env": os.environ.copy(),
            },
            "auth": {
                "cwd": project_root / "services" / "auth",
                "command": [sys.executable, "-m", "flask", "run", "--port", "8000"],
                "env": os.environ.copy(),
            },
            "web-client": {
                "cwd": project_root / "client",
                "command": (
                    ["npm", "run", "dev"]
                    if os.name != "nt"
                    else ["npm.cmd", "run", "dev"]
                ),
                "env": os.environ.copy(),
            },
            "file-watcher": {
                "cwd": project_root / "services" / "wiki",
                "command": [sys.executable, "-m", "app.sync", "watch"],
                "env": os.environ.copy(),
            },
        }

        service_config = service_commands.get(service_id)
        if not service_config:
            return {
                "success": False,
                "message": f"Service {service_id} cannot be started automatically",
            }

        try:
            # Start process in background
            if os.name == "nt":  # Windows
                # Use CREATE_NEW_CONSOLE to detach from parent
                process = subprocess.Popen(
                    service_config["command"],
                    cwd=str(service_config["cwd"]),
                    env=service_config["env"],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                    | subprocess.DETACHED_PROCESS,
                )
            else:  # Linux/Mac
                # Use nohup or start_new_session to detach
                process = subprocess.Popen(
                    service_config["command"],
                    cwd=str(service_config["cwd"]),
                    env=service_config["env"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )

            # Give it a moment to start
            time.sleep(0.5)

            # Verify it's still running
            if process.poll() is None:
                return {
                    "success": True,
                    "message": f"Service {service_id} started successfully",
                    "pid": process.pid,
                }
            else:
                return {
                    "success": False,
                    "message": f"Service {service_id} failed to start (exit code: {process.returncode})",
                }
        except FileNotFoundError:
            return {
                "success": False,
                "message": f"Command not found - ensure {service_id} dependencies are installed",
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error starting {service_id}: {str(e)}",
            }

    @staticmethod
    def restart_service(service_id: str) -> Dict:
        """
        Restart a service (stop then start).

        Args:
            service_id: Service identifier

        Returns:
            Dictionary with result: {'success': bool, 'message': str}
        """
        # Stop first
        stop_result = ServiceStatusService.stop_service(service_id)
        if (
            not stop_result.get("success")
            and "not running" not in stop_result.get("message", "").lower()
        ):
            # If stop failed for a reason other than "not running", return error
            return stop_result

        # Wait a moment for cleanup
        time.sleep(1)

        # Start
        start_result = ServiceStatusService.start_service(service_id)
        return start_result

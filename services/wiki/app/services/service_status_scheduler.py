"""
Background scheduler for automatically updating the service status page.

This module provides a background task that periodically updates the
Arcadium Service Status wiki page with current service health information.
"""

import logging
import threading
import uuid
from typing import Optional

from app.services.service_status_service import ServiceStatusService
from flask import Flask

logger = logging.getLogger(__name__)


class ServiceStatusScheduler:
    """
    Background scheduler for updating the service status page.

    Runs a periodic task that checks all services and updates the
    service status wiki page at regular intervals.

    Example:
        from app import create_app
        from app.services.service_status_scheduler import ServiceStatusScheduler

        app = create_app()
        scheduler = ServiceStatusScheduler(app, interval_minutes=10)
        scheduler.start()

        # ... app runs ...

        scheduler.stop()
    """

    def __init__(
        self,
        app: Flask,
        interval_minutes: int = 10,
        admin_user_id: Optional[uuid.UUID] = None,
    ):
        """
        Initialize the scheduler.

        Args:
            app: Flask application instance
            interval_minutes: Update interval in minutes (default: 10)
            admin_user_id: User ID to use for page updates (default: system admin)
        """
        self.app = app
        self.interval_minutes = interval_minutes
        self.interval_seconds = interval_minutes * 60
        self.admin_user_id = admin_user_id or uuid.UUID(
            "00000000-0000-0000-0000-000000000001"
        )
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False

    def _update_status_page(self):
        """Update the service status page with current health data."""
        try:
            with self.app.app_context():
                logger.info("Starting scheduled service status page update")

                # Check all services
                status_data = ServiceStatusService.check_all_services()

                # Update the page
                page = ServiceStatusService.create_or_update_status_page(
                    self.admin_user_id, status_data
                )

                logger.info(
                    f"Service status page updated successfully (page_id: {page.id}, "
                    f"slug: {page.slug})"
                )
        except Exception as e:
            logger.error(f"Error updating service status page: {e}", exc_info=True)

    def _run(self):
        """Main scheduler loop."""
        import datetime

        logger.info(
            f"Service status scheduler started (interval: {self.interval_minutes} minutes)"
        )

        # Run initial update immediately
        self._update_status_page()

        # Calculate seconds until next 10-minute interval (00, 10, 20, 30, 40, 50)
        now = datetime.datetime.now()
        current_minute = now.minute
        # Find next interval (round up to next 10-minute mark)
        next_interval_minute = ((current_minute // 10) + 1) * 10
        if next_interval_minute >= 60:
            # Next interval is in the next hour
            next_interval_minute = 0
            next_update = now.replace(
                minute=0, second=0, microsecond=0
            ) + datetime.timedelta(hours=1)
        else:
            next_update = now.replace(
                minute=next_interval_minute, second=0, microsecond=0
            )

        seconds_until_next = (next_update - now).total_seconds()
        logger.info(
            f"Next scheduled update at {next_update.strftime('%H:%M:%S')} "
            f"(in {int(seconds_until_next)} seconds)"
        )

        # Wait until the next 10-minute interval
        if self._stop_event.wait(timeout=seconds_until_next):
            # Stop was requested
            logger.info("Service status scheduler stopped")
            return

        # Now run on 10-minute intervals
        while not self._stop_event.is_set():
            # Update the page
            self._update_status_page()

            # Wait for the interval (or until stop is requested)
            if self._stop_event.wait(timeout=self.interval_seconds):
                # Stop was requested
                break

        logger.info("Service status scheduler stopped")

    def start(self):
        """Start the scheduler in a background thread."""
        if self._running:
            logger.warning("Scheduler is already running")
            return

        self._stop_event.clear()
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("Service status scheduler thread started")

    def stop(self):
        """Stop the scheduler."""
        if not self._running:
            return

        logger.info("Stopping service status scheduler...")
        self._stop_event.set()
        self._running = False

        if self._thread:
            self._thread.join(timeout=5.0)
            if self._thread.is_alive():
                logger.warning("Scheduler thread did not stop within timeout")
            else:
                logger.info("Service status scheduler stopped successfully")

    def is_running(self) -> bool:
        """Check if the scheduler is currently running."""
        return self._running and self._thread is not None and self._thread.is_alive()

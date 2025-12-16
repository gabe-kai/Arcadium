"""
Service status monitoring service.

Checks health of all Arcadium services and manages the service status page.
"""
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import requests
from flask import current_app
from app import db
from app.models.page import Page
from app.models.wiki_config import WikiConfig


class ServiceStatusService:
    """Service for monitoring and managing service status"""
    
    # Service definitions
    SERVICES = {
        'wiki': {
            'name': 'Wiki Service',
            'url': os.getenv('WIKI_SERVICE_URL', 'http://localhost:5000'),
            'health_endpoint': '/api/health'
        },
        'auth': {
            'name': 'Auth Service',
            'url': os.getenv('AUTH_SERVICE_URL', 'http://localhost:8000'),
            'health_endpoint': '/health'
        },
        'notification': {
            'name': 'Notification Service',
            'url': os.getenv('NOTIFICATION_SERVICE_URL', 'http://localhost:8006'),
            'health_endpoint': '/health'
        },
        'game-server': {
            'name': 'Game Server',
            'url': os.getenv('GAME_SERVER_URL', 'http://localhost:8080'),
            'health_endpoint': '/health'
        },
        'web-client': {
            'name': 'Web Client',
            'url': os.getenv('WEB_CLIENT_URL', 'http://localhost:3000'),
            'health_endpoint': '/health'
        },
        'admin': {
            'name': 'Admin Service',
            'url': os.getenv('ADMIN_SERVICE_URL', 'http://localhost:8001'),
            'health_endpoint': '/health'
        },
        'assets': {
            'name': 'Assets Service',
            'url': os.getenv('ASSETS_SERVICE_URL', 'http://localhost:8002'),
            'health_endpoint': '/health'
        },
        'chat': {
            'name': 'Chat Service',
            'url': os.getenv('CHAT_SERVICE_URL', 'http://localhost:8003'),
            'health_endpoint': '/health'
        },
        'leaderboard': {
            'name': 'Leaderboard Service',
            'url': os.getenv('LEADERBOARD_SERVICE_URL', 'http://localhost:8004'),
            'health_endpoint': '/health'
        },
        'presence': {
            'name': 'Presence Service',
            'url': os.getenv('PRESENCE_SERVICE_URL', 'http://localhost:8005'),
            'health_endpoint': '/health'
        }
    }
    
    @staticmethod
    def check_service_health(service_id: str, timeout: float = 5.0) -> Dict:
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
                'status': 'unhealthy',
                'response_time_ms': 0,
                'error': f'Unknown service: {service_id}',
                'details': {}
            }
        
        service = ServiceStatusService.SERVICES[service_id]
        url = f"{service['url']}{service['health_endpoint']}"
        
        start_time = time.time()
        try:
            response = requests.get(url, timeout=timeout)
            response_time_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'healthy')
                
                # Determine status based on response
                if status == 'healthy':
                    # Check response time thresholds
                    if response_time_ms > 1000:
                        status = 'unhealthy'
                    elif response_time_ms > 100:
                        status = 'degraded'
                
                return {
                    'status': status,
                    'response_time_ms': round(response_time_ms, 2),
                    'error': None,
                    'details': data
                }
            else:
                return {
                    'status': 'unhealthy',
                    'response_time_ms': round((time.time() - start_time) * 1000, 2),
                    'error': f'HTTP {response.status_code}',
                    'details': {}
                }
        except requests.exceptions.Timeout:
            return {
                'status': 'unhealthy',
                'response_time_ms': timeout * 1000,
                'error': 'Request timeout',
                'details': {}
            }
        except requests.exceptions.ConnectionError:
            return {
                'status': 'unhealthy',
                'response_time_ms': round((time.time() - start_time) * 1000, 2),
                'error': 'Connection refused',
                'details': {}
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'response_time_ms': round((time.time() - start_time) * 1000, 2),
                'error': str(e),
                'details': {}
            }
    
    @staticmethod
    def check_all_services() -> Dict[str, Dict]:
        """
        Check health of all services.
        
        Returns:
            Dictionary mapping service_id to health check results
        """
        results = {}
        for service_id in ServiceStatusService.SERVICES.keys():
            results[service_id] = ServiceStatusService.check_service_health(service_id)
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
        indicators = {
            'healthy': '🟢',
            'degraded': '🟡',
            'unhealthy': '🔴'
        }
        return indicators.get(status, '⚪')
    
    @staticmethod
    def get_status_display_name(status: str) -> str:
        """
        Get display name for status.
        
        Args:
            status: 'healthy', 'degraded', or 'unhealthy'
            
        Returns:
            Display name
        """
        names = {
            'healthy': 'Healthy',
            'degraded': 'Degraded',
            'unhealthy': 'Unhealthy'
        }
        return names.get(status, 'Unknown')
    
    @staticmethod
    def get_service_status_page() -> Optional[Page]:
        """
        Get the service status system page.
        
        Returns:
            Page object or None if not found
        """
        return db.session.query(Page).filter_by(
            slug='service-status',
            is_system_page=True
        ).first()
    
    @staticmethod
    def create_or_update_status_page(user_id: uuid.UUID, status_data: Dict[str, Dict]) -> Page:
        """
        Create or update the service status page with current status data.
        
        Args:
            user_id: User ID for page creation/update
            status_data: Dictionary of service_id -> health check results
            
        Returns:
            Page object
        """
        now = datetime.now(timezone.utc)
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        # Build markdown content
        content_lines = [
            "# Arcadium Service Status",
            "",
            f"*Last Updated: {timestamp}*",
            "",
            "## Services",
            "",
            "| Service | Status | Last Check | Response Time | Notes |",
            "|---------|--------|------------|---------------|-------|"
        ]
        
        # Add service rows
        for service_id, service_info in ServiceStatusService.SERVICES.items():
            health = status_data.get(service_id, {})
            status = health.get('status', 'unhealthy')
            indicator = ServiceStatusService.get_status_indicator(status)
            status_name = ServiceStatusService.get_status_display_name(status)
            response_time = health.get('response_time_ms', 0)
            response_time_str = f"{response_time}ms" if response_time > 0 else "N/A"
            error = health.get('error')
            notes = error if error else "-"
            
            content_lines.append(
                f"| {service_info['name']} | {indicator} {status_name} | {timestamp} | {response_time_str} | {notes} |"
            )
        
        content_lines.extend([
            "",
            "## Status Notes",
            "",
            "*Status checks run automatically. Manual updates can be made by administrators.*"
        ])
        
        # Add notes for non-healthy services
        has_notes = False
        for service_id, service_info in ServiceStatusService.SERVICES.items():
            health = status_data.get(service_id, {})
            status = health.get('status', 'unhealthy')
            if status != 'healthy':
                has_notes = True
                indicator = ServiceStatusService.get_status_indicator(status)
                error = health.get('error', 'Unknown issue')
                content_lines.append(f"### {service_info['name']} ({indicator} {ServiceStatusService.get_status_display_name(status)})")
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
                status='published',
                file_path="service-status.md"
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
                    notes[service_id] = {'notes': config.value}
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
                key=config_key,
                value=json.dumps(notes_data),
                updated_by=user_id
            )
            db.session.add(config)
        
        db.session.commit()

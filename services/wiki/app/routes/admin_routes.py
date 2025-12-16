"""Admin dashboard and configuration endpoints"""
import uuid
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify
from sqlalchemy import func

from app import db
from app.models.page import Page
from app.models.comment import Comment
from app.models.wiki_config import WikiConfig
from app.models.oversized_page_notification import OversizedPageNotification
from app.middleware.auth import require_auth, require_role
from app.services.size_monitoring_service import SizeMonitoringService
from app.services.service_status_service import ServiceStatusService


admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/dashboard/stats", methods=["GET"])
@require_auth
@require_role(["admin"])
def get_dashboard_stats():
    """Get basic admin dashboard statistics.

    Permissions: Admin
    """
    try:
        # Basic counts
        total_pages = db.session.query(func.count(Page.id)).scalar() or 0
        total_comments = db.session.query(func.count(Comment.id)).scalar() or 0

        # Distinct sections (non-null)
        total_sections = (
            db.session.query(func.count(func.distinct(Page.section)))
            .filter(Page.section.isnot(None))
            .scalar()
            or 0
        )

        # Storage usage in MB (sum of content_size_kb)
        total_kb = (
            db.session.query(func.coalesce(func.sum(Page.content_size_kb), 0.0)).scalar()
            or 0.0
        )
        storage_usage_mb = round(float(total_kb) / 1024.0, 2)

        # User counts - placeholder values (no user table in this service)
        total_users = {
            "viewers": 0,
            "players": 0,
            "writers": 0,
            "admins": 0,
        }

        # Recent activity - not tracked yet; return empty list
        recent_activity = []

        return (
            jsonify(
                {
                    "total_pages": int(total_pages),
                    "total_sections": int(total_sections),
                    "total_users": total_users,
                    "total_comments": int(total_comments),
                    "storage_usage_mb": storage_usage_mb,
                    "recent_activity": recent_activity,
                }
            ),
            200,
        )
    except Exception as e:  # pragma: no cover - defensive
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/admin/dashboard/size-distribution", methods=["GET"])
@require_auth
@require_role(["admin"])
def get_size_distribution():
    """Get page size and word count distribution buckets.

    Permissions: Admin
    """
    try:
        distribution = SizeMonitoringService.get_size_distribution()
        return jsonify(distribution), 200
    except Exception as e:  # pragma: no cover - defensive
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/admin/config/upload-size", methods=["POST"])
@require_auth
@require_role(["admin"])
def configure_upload_size():
    """Configure file upload size limit.

    Permissions: Admin
    """
    try:
        data = request.get_json() or {}
        max_size_mb = data.get("max_size_mb")
        is_custom = bool(data.get("is_custom", False))

        if max_size_mb is None:
            return jsonify({"error": "max_size_mb is required"}), 400

        try:
            max_size_mb_val = float(max_size_mb)
        except (ValueError, TypeError):
            return jsonify({"error": "max_size_mb must be a number"}), 400

        # Store in WikiConfig as simple key/value
        user_id = getattr(request, "user_id", None) or uuid.UUID(
            "00000000-0000-0000-0000-000000000001"
        )

        config = db.session.query(WikiConfig).filter_by(
            key="upload_max_size_mb"
        ).first()
        if not config:
            config = WikiConfig(
                key="upload_max_size_mb",
                value=str(max_size_mb_val),
                updated_by=user_id,
            )
            db.session.add(config)
        else:
            config.value = str(max_size_mb_val)
            config.updated_by = user_id

        # Track is_custom in a separate key
        custom_cfg = db.session.query(WikiConfig).filter_by(
            key="upload_max_size_is_custom"
        ).first()
        if not custom_cfg:
            custom_cfg = WikiConfig(
                key="upload_max_size_is_custom",
                value="true" if is_custom else "false",
                updated_by=user_id,
            )
            db.session.add(custom_cfg)
        else:
            custom_cfg.value = "true" if is_custom else "false"
            custom_cfg.updated_by = user_id

        db.session.commit()

        return (
            jsonify(
                {
                    "max_size_mb": max_size_mb_val,
                    "updated_at": config.updated_at.isoformat()
                    if config.updated_at
                    else None,
                }
            ),
            200,
        )
    except Exception as e:  # pragma: no cover - defensive
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/admin/config/page-size", methods=["POST"])
@require_auth
@require_role(["admin"])
def configure_page_size():
    """Configure page size limit.

    Permissions: Admin
    """
    try:
        data = request.get_json() or {}
        max_size_kb = data.get("max_size_kb")
        resolution_due_date = data.get("resolution_due_date")

        if max_size_kb is None:
            return jsonify({"error": "max_size_kb is required"}), 400
        if not resolution_due_date:
            return jsonify({"error": "resolution_due_date is required"}), 400

        try:
            max_size_kb_val = float(max_size_kb)
        except (ValueError, TypeError):
            return jsonify({"error": "max_size_kb must be a number"}), 400

        # Parse resolution due date to ensure it's valid ISO format
        try:
            datetime.fromisoformat(resolution_due_date.replace("Z", "+00:00"))
        except ValueError:
            return jsonify(
                {"error": "resolution_due_date must be ISO 8601 datetime"}
            ), 400

        user_id = getattr(request, "user_id", None) or uuid.UUID(
            "00000000-0000-0000-0000-000000000001"
        )

        config = db.session.query(WikiConfig).filter_by(
            key="page_max_size_kb"
        ).first()
        if not config:
            config = WikiConfig(
                key="page_max_size_kb",
                value=str(max_size_kb_val),
                updated_by=user_id,
            )
            db.session.add(config)
        else:
            config.value = str(max_size_kb_val)
            config.updated_by = user_id

        db.session.commit()

        # Parse resolution due date
        try:
            due_date = datetime.fromisoformat(resolution_due_date.replace("Z", "+00:00"))
        except ValueError:
            due_date = datetime.fromisoformat(resolution_due_date)

        # Create oversized page notifications
        notifications = SizeMonitoringService.create_oversized_notifications(
            max_size_kb=max_size_kb_val,
            resolution_due_date=due_date
        )

        return (
            jsonify(
                {
                    "max_size_kb": max_size_kb_val,
                    "resolution_due_date": resolution_due_date,
                    "oversized_pages_count": len(notifications),
                    "notifications_created": len(notifications),
                    "updated_at": config.updated_at.isoformat()
                    if config.updated_at
                    else None,
                }
            ),
            200,
        )
    except Exception as e:  # pragma: no cover - defensive
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/admin/oversized-pages", methods=["GET"])
@require_auth
@require_role(["admin"])
def get_oversized_pages():
    """Get list of oversized pages based on notifications.

    Permissions: Admin
    """
    try:
        pages = SizeMonitoringService.get_oversized_pages_with_notifications()
        
        # Add authors field (placeholder - no user model in this service)
        for page in pages:
            page['authors'] = []
        
        return jsonify({"pages": pages}), 200
    except Exception as e:  # pragma: no cover - defensive
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/admin/oversized-pages/<uuid:page_id>/status", methods=["PUT"])
@require_auth
@require_role(["admin"])
def update_oversized_page_status(page_id):
    """Update status for an oversized page notification.

    Permissions: Admin
    """
    try:
        data = request.get_json() or {}
        status = data.get("status")
        extend_due_date = data.get("extend_due_date")

        if not status:
            return jsonify({"error": "status is required"}), 400

        # Find latest notification by page_id
        notif = (
            db.session.query(OversizedPageNotification)
            .filter_by(page_id=page_id)
            .order_by(OversizedPageNotification.created_at.desc())
            .first()
        )
        if not notif:
            return (
                jsonify(
                    {"error": f"No oversized notification found for page {page_id}"}
                ),
                404,
            )

        # Update resolved flag based on status
        if status == "resolved":
            notif.resolved = True
            notif.resolved_at = datetime.now(timezone.utc)
        else:
            # For other statuses, keep resolved False
            notif.resolved = False

        # Optionally extend due date
        if extend_due_date:
            try:
                new_due = datetime.fromisoformat(extend_due_date.replace("Z", "+00:00"))
                notif.resolution_due_date = new_due
            except ValueError:
                return (
                    jsonify(
                        {
                            "error": "extend_due_date must be ISO 8601 datetime",
                        }
                    ),
                    400,
                )

        db.session.commit()

        return (
            jsonify(
                {
                    "page_id": str(notif.page_id),
                    "status": status,
                    "due_date": notif.resolution_due_date.isoformat()
                    if notif.resolution_due_date
                    else None,
                    "resolved": notif.resolved,
                }
            ),
            200,
        )
    except Exception as e:  # pragma: no cover - defensive
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/admin/service-status", methods=["GET"])
@require_auth
@require_role(["admin"])
def get_service_status():
    """Get service status for all Arcadium services.

    Permissions: Admin
    """
    try:
        # Check all services
        status_data = ServiceStatusService.check_all_services()
        
        # Get manual notes
        manual_notes = ServiceStatusService.get_manual_status_notes()
        
        # Format response
        services = {}
        for service_id, service_info in ServiceStatusService.SERVICES.items():
            health = status_data.get(service_id, {})
            services[service_id] = {
                "name": service_info["name"],
                "status": health.get("status", "unhealthy"),
                "last_check": datetime.now(timezone.utc).isoformat(),
                "response_time_ms": health.get("response_time_ms", 0),
                "error": health.get("error"),
                "details": health.get("details", {}),
                "manual_notes": manual_notes.get(service_id)
            }
        
        return jsonify({
            "services": services,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }), 200
    except Exception as e:  # pragma: no cover - defensive
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/admin/service-status", methods=["PUT"])
@require_auth
@require_role(["admin"])
def update_service_status():
    """Update service status with manual notes (for maintenance windows, etc.).

    Permissions: Admin
    """
    try:
        data = request.get_json() or {}
        service_id = data.get("service")
        notes_data = data.get("notes", {})
        
        if not service_id:
            return jsonify({"error": "service is required"}), 400
        
        if service_id not in ServiceStatusService.SERVICES:
            return jsonify({"error": f"Unknown service: {service_id}"}), 400
        
        user_id = getattr(request, "user_id", None) or uuid.UUID(
            "00000000-0000-0000-0000-000000000001"
        )
        
        # Set manual notes
        ServiceStatusService.set_manual_status_notes(service_id, notes_data, user_id)
        
        return jsonify({
            "success": True,
            "message": "Status updated",
            "service": service_id,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }), 200
    except Exception as e:  # pragma: no cover - defensive
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/admin/service-status/refresh", methods=["POST"])
@require_auth
@require_role(["admin"])
def refresh_service_status_page():
    """Refresh the service status page with current health check data.

    Permissions: Admin
    """
    try:
        user_id = getattr(request, "user_id", None) or uuid.UUID(
            "00000000-0000-0000-0000-000000000001"
        )
        
        # Check all services
        status_data = ServiceStatusService.check_all_services()
        
        # Create or update the status page
        page = ServiceStatusService.create_or_update_status_page(user_id, status_data)
        
        return jsonify({
            "success": True,
            "message": "Service status page updated",
            "page_id": str(page.id),
            "page_slug": page.slug,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }), 200
    except Exception as e:  # pragma: no cover - defensive
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

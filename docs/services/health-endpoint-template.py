"""
Health Endpoint Template for Arcadium Services

Copy this template to your service and customize as needed.

1. Copy health_check.py utility:
   cp services/wiki/app/utils/health_check.py services/your-service/app/utils/

2. Add this health endpoint to your service's routes or __init__.py
3. Customize service_name and version
4. Add any service-specific additional_info
"""

from app.utils.health_check import get_health_status
from flask import Blueprint, jsonify

# If adding to a blueprint:
bp = Blueprint("health", __name__)


@bp.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint with process information.

    Returns standardized health status including process metadata.
    """
    health_status = get_health_status(
        service_name="your-service-name",  # Change this!
        version="1.0.0",  # Change this!
        additional_info={
            # Add service-specific information here
            # Examples:
            # "database": "connected",
            # "cache": "operational",
            # "queue_size": 0,
        },
        include_process_info=True,
    )

    return jsonify(health_status), 200


# If adding directly to app (in __init__.py):
"""
@app.route("/health")
def health():
    from app.utils.health_check import get_health_status
    from flask import jsonify

    health_status = get_health_status(
        service_name="your-service-name",
        version="1.0.0",
        include_process_info=True,
    )

    return jsonify(health_status), 200
"""

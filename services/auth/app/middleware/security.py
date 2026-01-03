"""Security headers middleware"""

from flask import request


def add_security_headers(response):
    """
    Add security headers to all responses.

    Headers:
    - X-Content-Type-Options: nosniff - Prevents MIME type sniffing
    - X-Frame-Options: DENY - Prevents clickjacking
    - X-XSS-Protection: 1; mode=block - Enables XSS filtering
    - Strict-Transport-Security: Only added in production with HTTPS
    """
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Only add HSTS in production with HTTPS
    # This should be handled by the reverse proxy in production,
    # but we can add it here as well if needed
    if request.is_secure:
        from flask import current_app

        if not current_app.debug:
            # HSTS: max-age=31536000 (1 year), includeSubDomains
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

    return response

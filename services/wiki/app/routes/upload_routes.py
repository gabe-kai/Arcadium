"""File upload endpoints (images)."""
import os
import uuid

from flask import Blueprint, request, jsonify, current_app, send_from_directory

from app import db
from app.models.page import Page
from app.models.image import Image, PageImage
from app.models.wiki_config import WikiConfig
from app.middleware.auth import require_auth, require_role


upload_bp = Blueprint("upload", __name__)


def _get_max_upload_size_bytes() -> int:
    """Get max upload size in bytes from WikiConfig (upload_max_size_mb), default 10MB."""
    default_mb = 10.0
    config = db.session.query(WikiConfig).filter_by(key="upload_max_size_mb").first()
    if not config:
        max_mb = default_mb
    else:
        try:
            max_mb = float(config.value)
        except (TypeError, ValueError):
            max_mb = default_mb
    return int(max_mb * 1024 * 1024)


@upload_bp.route("/upload/image", methods=["POST"])
@require_auth
@require_role(["writer", "admin"])
def upload_image():
    """Upload an image file.

    Permissions: Writer, Admin
    """
    try:
        if "file" not in request.files:
            return jsonify({"error": "file field is required"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        # Read file content into memory to get size and write later
        data = file.read()
        size_bytes = len(data)

        # Validate size against config
        max_bytes = _get_max_upload_size_bytes()
        if size_bytes > max_bytes:
            return (
                jsonify(
                    {
                        "error": "File too large",
                        "max_size_bytes": max_bytes,
                        "size_bytes": size_bytes,
                    }
                ),
                400,
            )

        # Optional page association
        page_id_str = request.form.get("page_id") or request.args.get("page_id")
        page_id = None
        if page_id_str:
            try:
                page_uuid = uuid.UUID(page_id_str)
            except ValueError:
                return jsonify({"error": "Invalid page_id format"}), 400

            page = db.session.get(Page, page_uuid)
            if not page:
                return jsonify({"error": f"Page not found: {page_id_str}"}), 404
            page_id = page_uuid

        # Generate UUID-based filename
        image_uuid = uuid.uuid4()
        orig_filename = file.filename
        _, ext = os.path.splitext(orig_filename)
        ext = ext or ""
        filename = f"{image_uuid}{ext}"

        # Determine upload directory
        uploads_dir = current_app.config.get("WIKI_UPLOADS_DIR", "data/uploads/images")
        os.makedirs(uploads_dir, exist_ok=True)

        # Save file to disk
        full_path = os.path.join(uploads_dir, filename)
        with open(full_path, "wb") as f:
            f.write(data)

        # Build URL relative to uploads directory
        url = f"/uploads/images/{filename}"

        # Create Image record
        user_id = getattr(request, "user_id", None) or uuid.UUID(
            "00000000-0000-0000-0000-000000000001"
        )

        image = Image(
            uuid=str(image_uuid),
            original_filename=orig_filename,
            file_path=full_path,
            mime_type=file.mimetype,
            size_bytes=size_bytes,
            uploaded_by=user_id,
        )
        db.session.add(image)
        db.session.flush()  # Get image.id

        # Optional PageImage association
        if page_id:
            page_image = PageImage(page_id=page_id, image_id=image.id)
            db.session.add(page_image)

        db.session.commit()

        return (
            jsonify(
                {
                    "url": url,
                    "uuid": str(image_uuid),
                    "original_filename": orig_filename,
                    "size": size_bytes,
                    "mime_type": file.mimetype,
                    "page_id": str(page_id) if page_id else None,
                }
            ),
            200,
        )
    except Exception as e:  # pragma: no cover - defensive
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@upload_bp.route("/uploads/images/<filename>", methods=["GET"])
def serve_image(filename):
    """Serve uploaded image files.
    
    Public endpoint - no authentication required for viewing images.
    """
    try:
        uploads_dir = current_app.config.get("WIKI_UPLOADS_DIR", "data/uploads/images")
        return send_from_directory(uploads_dir, filename)
    except FileNotFoundError:
        return jsonify({"error": "Image not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500



"""File upload endpoints (images)."""
import os
import uuid

from flask import Blueprint, request, jsonify, current_app, send_file, send_from_directory
from werkzeug.exceptions import NotFound
import logging

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
        # Ensure absolute path for consistency
        uploads_dir = os.path.abspath(uploads_dir)
        os.makedirs(uploads_dir, exist_ok=True)

        # Save file to disk
        full_path = os.path.join(uploads_dir, filename)
        # Normalize path for Windows compatibility
        full_path = os.path.normpath(full_path)
        with open(full_path, "wb") as f:
            f.write(data)
        
        # Verify file was saved correctly
        file_saved = os.path.exists(full_path)
        file_size_saved = os.path.getsize(full_path) if file_saved else 0
        logging.info(f"Image saved: filename={filename}, full_path={full_path}, saved={file_saved}, size={file_size_saved}, expected_size={size_bytes}")
        
        if not file_saved or file_size_saved != size_bytes:
            logging.error(f"File save verification failed: exists={file_saved}, size={file_size_saved}, expected={size_bytes}")
            return jsonify({"error": "Failed to save image file"}), 500

        # Build URL relative to API base (blueprint is registered under /api)
        url = f"/api/uploads/images/{filename}"

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
        # Convert to absolute path
        uploads_dir = os.path.abspath(uploads_dir)
        
        # Ensure the directory exists
        if not os.path.exists(uploads_dir):
            logging.error(f"Uploads directory not found: {uploads_dir}")
            return jsonify({"error": "Uploads directory not found"}), 404
        
        # Build full file path
        file_path = os.path.join(uploads_dir, filename)
        # Normalize path separators for Windows
        file_path = os.path.normpath(file_path)
        
        # Security check: ensure file is within uploads directory
        if not os.path.abspath(file_path).startswith(os.path.abspath(uploads_dir)):
            logging.error(f"Security violation: attempted to access file outside uploads directory: {file_path}")
            return jsonify({"error": "Invalid file path"}), 403
        
        # Check if file exists
        if not os.path.exists(file_path):
            logging.error(f"Image file not found: {file_path} (uploads_dir: {uploads_dir}, filename: {filename})")
            # List files in directory for debugging
            try:
                existing_files = os.listdir(uploads_dir)
                logging.error(f"Files in uploads_dir: {existing_files[:10]}")
            except Exception:
                pass
            return jsonify({"error": "Image not found"}), 404
        
        # Determine MIME type from file extension
        mime_type = 'image/png'
        if filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
            mime_type = 'image/jpeg'
        elif filename.lower().endswith('.gif'):
            mime_type = 'image/gif'
        elif filename.lower().endswith('.webp'):
            mime_type = 'image/webp'
        elif filename.lower().endswith('.svg'):
            mime_type = 'image/svg+xml'
        
        # Log before serving - detailed info
        file_exists = os.path.exists(file_path)
        file_size = os.path.getsize(file_path) if file_exists else 0
        logging.info(f"Serving image: filename={filename}, file_path={file_path}, exists={file_exists}, size={file_size}, uploads_dir={uploads_dir}")
        
        # Double-check file exists before serving
        if not file_exists:
            logging.error(f"File does not exist when trying to serve: {file_path}")
            return jsonify({"error": "Image not found"}), 404
        
        # Use send_file directly with absolute path - more reliable than send_from_directory
        # send_from_directory can have issues with Windows paths and safe_join
        try:
            # Use absolute path for send_file
            file_path_abs = os.path.abspath(file_path)
            logging.info(f"Serving with send_file: {file_path_abs}")
            response = send_file(
                file_path_abs,
                mimetype=mime_type,
                as_attachment=False
            )
            # Add CORS headers for image serving
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
            return response
        except NotFound as not_found_error:
            # send_file raises NotFound if file doesn't exist
            logging.error(f"send_file NotFound for {filename}: {str(not_found_error)}")
            logging.error(f"File path checked: {file_path_abs}, exists: {os.path.exists(file_path_abs)}")
            return jsonify({"error": "Image not found"}), 404
        except Exception as send_error:
            logging.error(f"Error in send_file for {file_path_abs}: {str(send_error)}", exc_info=True)
            raise
    except FileNotFoundError as e:
        logging.error(f"FileNotFoundError serving image {filename}: {str(e)}")
        return jsonify({"error": "Image not found"}), 404
    except Exception as e:
        logging.error(f"Error serving image {filename}: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500



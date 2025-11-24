# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Heikki Toivonen

import logging
import os
from io import BytesIO

from flask import Blueprint, Response, jsonify, render_template, request
from flask_login import login_required
from PIL import Image
from werkzeug.utils import secure_filename

from app import db
from app.models import Floorplan, Resource

logger = logging.getLogger(__name__)

main = Blueprint("main", __name__)

UPLOAD_FOLDER = "app/static/floorplans"
# Removed SVG to prevent XSS attacks (SVG can contain scripts)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
ALLOWED_FORMATS = {"PNG", "JPEG", "GIF"}  # PIL format names


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_image(stream) -> bool:
    """
    Validate that uploaded file is actually an image by checking file content.

    This prevents attackers from uploading malicious files with image extensions.
    Uses PIL/Pillow to verify the file is a valid image.
    """
    try:
        # Read the stream into memory
        stream.seek(0)
        img_data = stream.read()
        stream.seek(0)

        # Try to open and verify the image
        img = Image.open(BytesIO(img_data))
        img.verify()  # Verify it's a valid image

        # Check if format is allowed
        if img.format not in ALLOWED_FORMATS:
            return False

        return True
    except Exception:
        return False


@main.route("/")
def index() -> str:
    return render_template("index.html")


@main.route("/admin")
@login_required
def admin() -> str:
    return render_template("admin.html")


@main.route("/api/search", methods=["GET"])
def search() -> Response | tuple[Response, int]:
    query = request.args.get("q", "").strip()

    if not query:
        return jsonify({"error": "Search query is required"}), 400

    resources = Resource.query.filter(Resource.name.ilike(f"%{query}%")).all()

    if not resources:
        return (
            jsonify(
                {
                    "error": f'No resources matching "{query}" found',
                    "message": "Please try a different search term",
                }
            ),
            404,
        )

    # Build results with floorplan info
    results = []
    for resource in resources:
        floorplan = Floorplan.query.get(resource.floorplan_id)
        results.append(
            {
                "resource": resource.to_dict(),
                "floorplan": floorplan.to_dict() if floorplan else None,
            }
        )

    return jsonify({"count": len(results), "results": results})


@main.route("/api/floorplans", methods=["GET", "POST"])
@login_required
def floorplans() -> Response | tuple[Response, int]:
    if request.method == "POST":
        # Handle file upload
        if "image" in request.files:
            file = request.files["image"]
            name = request.form.get("name")

            if not name:
                return jsonify({"error": "Floorplan name is required"}), 400

            if file.filename == "":
                return jsonify({"error": "No file selected"}), 400

            if file and file.filename and allowed_file(file.filename):
                # Validate file content to ensure it's actually an image
                if not validate_image(file.stream):
                    return jsonify({"error": "Invalid file content. File must be a valid image."}), 400

                filename = secure_filename(file.filename)
                # Add timestamp to filename to avoid conflicts
                import time

                filename = f"{int(time.time())}_{filename}"

                # Ensure upload folder exists
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)

                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)

                floorplan = Floorplan(name=name, image_filename=filename)
                db.session.add(floorplan)
                db.session.commit()
                return jsonify(floorplan.to_dict()), 201
            else:
                return (
                    jsonify({"error": "Invalid file type. Allowed: png, jpg, jpeg, gif"}),
                    400,
                )
        else:
            # JSON-based creation (for backwards compatibility)
            data = request.get_json()
            floorplan = Floorplan(name=data.get("name"), image_filename=data.get("image_filename"))
            db.session.add(floorplan)
            db.session.commit()
            return jsonify(floorplan.to_dict()), 201

    floorplans = Floorplan.query.all()
    return jsonify([floorplan.to_dict() for floorplan in floorplans])


@main.route("/api/floorplans/<int:floorplan_id>", methods=["GET", "PUT", "DELETE"])
@login_required
def floorplan_detail(floorplan_id: int) -> Response | tuple[str, int]:
    floorplan = Floorplan.query.get_or_404(floorplan_id)

    if request.method == "DELETE":
        # Delete the image file from filesystem
        image_path = os.path.join(UPLOAD_FOLDER, floorplan.image_filename)
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            # Log the error but continue with database deletion
            logger.warning(f"Failed to delete image file {image_path}: {e}")

        # Delete from database (this will cascade to resources)
        db.session.delete(floorplan)
        db.session.commit()
        return "", 204

    if request.method == "PUT":
        data = request.get_json()
        floorplan.name = data.get("name", floorplan.name)
        floorplan.image_filename = data.get("image_filename", floorplan.image_filename)
        db.session.commit()
        return jsonify(floorplan.to_dict())

    return jsonify(floorplan.to_dict())


@main.route("/api/resources", methods=["GET", "POST"])
@login_required
def resources() -> Response | tuple[Response, int]:
    if request.method == "POST":
        data = request.get_json()
        resource = Resource(
            name=data.get("name"),
            type=data.get("type"),
            x_coordinate=data.get("x_coordinate"),
            y_coordinate=data.get("y_coordinate"),
            floorplan_id=data.get("floorplan_id"),
        )

        # Set type-specific metadata
        resource_type = data.get("type")
        if resource_type == "room":
            resource.room_number = data.get("room_number")
            resource.room_type = data.get("room_type")
            resource.capacity = data.get("capacity")
        elif resource_type == "printer":
            resource.printer_name = data.get("printer_name")
            resource.color_type = data.get("color_type")
            resource.printer_model = data.get("printer_model")
        elif resource_type == "person":
            resource.email = data.get("email")
            resource.title = data.get("title")
        elif resource_type == "bathroom":
            resource.gender_type = data.get("gender_type")

        db.session.add(resource)
        db.session.commit()
        return jsonify(resource.to_dict()), 201

    resources = Resource.query.all()
    return jsonify([resource.to_dict() for resource in resources])


@main.route("/api/resources/<int:resource_id>", methods=["GET", "PUT", "DELETE"])
@login_required
def resource_detail(resource_id: int) -> Response | tuple[str, int]:
    resource = Resource.query.get_or_404(resource_id)

    if request.method == "DELETE":
        db.session.delete(resource)
        db.session.commit()
        return "", 204

    if request.method == "PUT":
        data = request.get_json()
        resource.name = data.get("name", resource.name)
        resource.type = data.get("type", resource.type)
        resource.x_coordinate = data.get("x_coordinate", resource.x_coordinate)
        resource.y_coordinate = data.get("y_coordinate", resource.y_coordinate)
        resource.floorplan_id = data.get("floorplan_id", resource.floorplan_id)

        # Update type-specific metadata
        resource_type = data.get("type", resource.type)
        if resource_type == "room":
            resource.room_number = data.get("room_number", resource.room_number)
            resource.room_type = data.get("room_type", resource.room_type)
            resource.capacity = data.get("capacity", resource.capacity)
            # Clear other type-specific fields
            resource.printer_name = None
            resource.color_type = None
            resource.printer_model = None
            resource.email = None
            resource.title = None
            resource.gender_type = None
        elif resource_type == "printer":
            resource.printer_name = data.get("printer_name", resource.printer_name)
            resource.color_type = data.get("color_type", resource.color_type)
            resource.printer_model = data.get("printer_model", resource.printer_model)
            # Clear other type-specific fields
            resource.room_number = None
            resource.room_type = None
            resource.capacity = None
            resource.email = None
            resource.title = None
            resource.gender_type = None
        elif resource_type == "person":
            resource.email = data.get("email", resource.email)
            resource.title = data.get("title", resource.title)
            # Clear other type-specific fields
            resource.room_number = None
            resource.room_type = None
            resource.capacity = None
            resource.printer_name = None
            resource.color_type = None
            resource.printer_model = None
            resource.gender_type = None
        elif resource_type == "bathroom":
            resource.gender_type = data.get("gender_type", resource.gender_type)
            # Clear other type-specific fields
            resource.room_number = None
            resource.room_type = None
            resource.capacity = None
            resource.printer_name = None
            resource.color_type = None
            resource.printer_model = None
            resource.email = None
            resource.title = None

        db.session.commit()
        return jsonify(resource.to_dict())

    return jsonify(resource.to_dict())

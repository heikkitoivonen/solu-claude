import os

from flask import Blueprint, Response, jsonify, render_template, request
from flask_login import login_required
from werkzeug.utils import secure_filename

from app import db
from app.models import Floorplan, Resource

main = Blueprint("main", __name__)

UPLOAD_FOLDER = "app/static/floorplans"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "svg"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


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
                    jsonify({"error": "Invalid file type. Allowed: png, jpg, jpeg, gif, svg"}),
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
def floorplan_detail(floorplan_id: int) -> Response | tuple[str, int]:
    floorplan = Floorplan.query.get_or_404(floorplan_id)

    if request.method == "DELETE":
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
        db.session.add(resource)
        db.session.commit()
        return jsonify(resource.to_dict()), 201

    resources = Resource.query.all()
    return jsonify([resource.to_dict() for resource in resources])


@main.route("/api/resources/<int:resource_id>", methods=["GET", "PUT", "DELETE"])
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
        db.session.commit()
        return jsonify(resource.to_dict())

    return jsonify(resource.to_dict())

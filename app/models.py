from datetime import datetime
from typing import Any

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


class User(UserMixin, db.Model):  # type: ignore[name-defined]
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    password_must_change = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<User {self.username}>"

    def set_password(self, password: str) -> None:
        """Set password hash from plain text password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check if provided password matches hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_admin": self.is_admin,
            "password_must_change": self.password_must_change,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Floorplan(db.Model):  # type: ignore[name-defined]
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    image_filename = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resources = db.relationship(
        "Resource", backref="floorplan", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Floorplan {self.name}>"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "image_filename": self.image_filename,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Resource(db.Model):  # type: ignore[name-defined]
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    x_coordinate = db.Column(db.Integer, nullable=False)
    y_coordinate = db.Column(db.Integer, nullable=False)
    floorplan_id = db.Column(db.Integer, db.ForeignKey("floorplan.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Resource {self.name} ({self.type})>"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "x_coordinate": self.x_coordinate,
            "y_coordinate": self.y_coordinate,
            "floorplan_id": self.floorplan_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

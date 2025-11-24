# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Heikki Toivonen

"""
Tests for database models.
"""

from app import db
from app.models import Floorplan, Resource


class TestFloorplan:
    """Tests for Floorplan model."""

    def test_create_floorplan(self, app):
        """Test creating a floorplan."""
        with app.app_context():
            floorplan = Floorplan(name="First Floor", image_filename="floor1.png")
            db.session.add(floorplan)
            db.session.commit()

            assert floorplan.id is not None
            assert floorplan.name == "First Floor"
            assert floorplan.image_filename == "floor1.png"
            assert floorplan.created_at is not None

    def test_floorplan_repr(self, app, sample_floorplan):
        """Test floorplan __repr__ method."""
        with app.app_context():
            floorplan = Floorplan.query.get(sample_floorplan.id)
            assert repr(floorplan) == "<Floorplan Test Floor>"

    def test_floorplan_to_dict(self, app, sample_floorplan):
        """Test floorplan to_dict method."""
        with app.app_context():
            floorplan = Floorplan.query.get(sample_floorplan.id)
            data = floorplan.to_dict()
            assert data["id"] == sample_floorplan.id
            assert data["name"] == "Test Floor"
            assert data["image_filename"] == "test_floor.png"
            assert "created_at" in data

    def test_floorplan_cascade_delete(self, app, sample_floorplan):
        """Test that deleting a floorplan deletes its resources."""
        with app.app_context():
            # Add resource to floorplan
            resource = Resource(
                name="Test Resource",
                type="room",
                x_coordinate=100,
                y_coordinate=100,
                floorplan_id=sample_floorplan.id,
            )
            db.session.add(resource)
            db.session.commit()

            resource_id = resource.id
            floorplan_id = sample_floorplan.id

            # Delete floorplan - query it fresh first
            floorplan = Floorplan.query.get(floorplan_id)
            db.session.delete(floorplan)
            db.session.commit()

            # Check floorplan is deleted
            assert Floorplan.query.get(floorplan_id) is None
            # Check resource is also deleted (cascade)
            assert Resource.query.get(resource_id) is None


class TestResource:
    """Tests for Resource model."""

    def test_create_resource(self, app, sample_floorplan):
        """Test creating a resource."""
        with app.app_context():
            resource = Resource(
                name="Conference Room",
                type="room",
                x_coordinate=250,
                y_coordinate=180,
                floorplan_id=sample_floorplan.id,
            )
            db.session.add(resource)
            db.session.commit()

            assert resource.id is not None
            assert resource.name == "Conference Room"
            assert resource.type == "room"
            assert resource.x_coordinate == 250
            assert resource.y_coordinate == 180
            assert resource.floorplan_id == sample_floorplan.id
            assert resource.created_at is not None

    def test_resource_repr(self, app, sample_resource):
        """Test resource __repr__ method."""
        with app.app_context():
            resource = Resource.query.get(sample_resource.id)
            assert repr(resource) == "<Resource Test Room (room)>"

    def test_resource_to_dict(self, app, sample_resource):
        """Test resource to_dict method."""
        with app.app_context():
            resource = Resource.query.get(sample_resource.id)
            data = resource.to_dict()
            assert data["id"] == sample_resource.id
            assert data["name"] == "Test Room"
            assert data["type"] == "room"
            assert data["x_coordinate"] == 100
            assert data["y_coordinate"] == 200
            assert data["floorplan_id"] == sample_resource.floorplan_id
            assert "created_at" in data

    def test_resource_relationship(self, app, sample_resource):
        """Test resource-floorplan relationship."""
        with app.app_context():
            resource = Resource.query.get(sample_resource.id)
            assert resource.floorplan is not None
            assert resource.floorplan.name == "Test Floor"

    def test_floorplan_resources_relationship(self, app, sample_floorplan):
        """Test floorplan.resources relationship."""
        with app.app_context():
            floorplan = Floorplan.query.get(sample_floorplan.id)

            # Add resources
            resource1 = Resource(
                name="Room 1",
                type="room",
                x_coordinate=100,
                y_coordinate=100,
                floorplan_id=floorplan.id,
            )
            resource2 = Resource(
                name="Room 2",
                type="room",
                x_coordinate=200,
                y_coordinate=200,
                floorplan_id=floorplan.id,
            )
            db.session.add(resource1)
            db.session.add(resource2)
            db.session.commit()

            # Check relationship
            floorplan = Floorplan.query.get(sample_floorplan.id)
            assert len(floorplan.resources) == 2
            resource_names = [r.name for r in floorplan.resources]
            assert "Room 1" in resource_names
            assert "Room 2" in resource_names

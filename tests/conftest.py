# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Heikki Toivonen

"""
Pytest configuration and fixtures for testing.
"""

import pytest

from app import create_app, db
from app.models import Floorplan, Resource, User


@pytest.fixture
def app():
    """Create application for testing with in-memory database."""
    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,  # Disable CSRF for testing
        "SECRET_KEY": "test-secret-key",
    }

    app = create_app(config)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
        # Dispose of the database engine to close all connections
        db.engine.dispose()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create CLI test runner."""
    return app.test_cli_runner()


@pytest.fixture
def sample_floorplan(app):
    """Create a sample floorplan for testing."""
    with app.app_context():
        floorplan = Floorplan(name="Test Floor", image_filename="test_floor.png")
        db.session.add(floorplan)
        db.session.commit()
        floorplan_id = floorplan.id

    # Return a simple object with the ID that can be accessed outside the context
    class FloorplanData:
        def __init__(self, id):
            self.id = id

    return FloorplanData(floorplan_id)


@pytest.fixture
def sample_resource(app, sample_floorplan):
    """Create a sample resource for testing."""
    with app.app_context():
        resource = Resource(
            name="Test Room",
            type="room",
            x_coordinate=100,
            y_coordinate=200,
            floorplan_id=sample_floorplan.id,
        )
        db.session.add(resource)
        db.session.commit()
        resource_id = resource.id
        floorplan_id = resource.floorplan_id

    class ResourceData:
        def __init__(self, id, floorplan_id):
            self.id = id
            self.floorplan_id = floorplan_id

    return ResourceData(resource_id, floorplan_id)


@pytest.fixture
def multiple_resources(app, sample_floorplan):
    """Create multiple resources for testing search."""
    with app.app_context():
        resources = [
            Resource(
                name="Conference Room A",
                type="room",
                x_coordinate=150,
                y_coordinate=100,
                floorplan_id=sample_floorplan.id,
            ),
            Resource(
                name="Conference Room B",
                type="room",
                x_coordinate=350,
                y_coordinate=100,
                floorplan_id=sample_floorplan.id,
            ),
            Resource(
                name="Printer 1",
                type="printer",
                x_coordinate=200,
                y_coordinate=250,
                floorplan_id=sample_floorplan.id,
            ),
        ]
        for resource in resources:
            db.session.add(resource)
        db.session.commit()

    return None  # Just need the data to be in the database


@pytest.fixture
def admin_user(app):
    """Create an admin user for testing."""
    with app.app_context():
        user = User(username="testadmin", is_admin=True, password_must_change=False)
        user.set_password("Admin123!@#")
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    class UserData:
        def __init__(self, id, username):
            self.id = id
            self.username = username

    return UserData(user_id, "testadmin")


@pytest.fixture
def admin_user_must_change(app):
    """Create an admin user who must change password."""
    with app.app_context():
        user = User(username="newadmin", is_admin=True, password_must_change=True)
        user.set_password("Admin123!@#")
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    class UserData:
        def __init__(self, id, username):
            self.id = id
            self.username = username

    return UserData(user_id, "newadmin")


@pytest.fixture
def regular_user(app):
    """Create a non-admin user for testing."""
    with app.app_context():
        user = User(username="regularuser", is_admin=False, password_must_change=False)
        user.set_password("Regular123!@#")
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    class UserData:
        def __init__(self, id, username):
            self.id = id
            self.username = username

    return UserData(user_id, "regularuser")

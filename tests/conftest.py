"""
Pytest configuration and fixtures for testing.
"""
import pytest
import tempfile
import os
from app import create_app, db
from app.models import Floorplan, Resource


@pytest.fixture
def app():
    """Create application for testing."""
    db_fd, db_path = tempfile.mkstemp()

    config = {
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing
        'SECRET_KEY': 'test-secret-key'
    }

    app = create_app(config)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

    os.close(db_fd)
    os.unlink(db_path)


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
        floorplan = Floorplan(
            name='Test Floor',
            image_filename='test_floor.png'
        )
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
            name='Test Room',
            type='room',
            x_coordinate=100,
            y_coordinate=200,
            floorplan_id=sample_floorplan.id
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
                name='Conference Room A',
                type='room',
                x_coordinate=150,
                y_coordinate=100,
                floorplan_id=sample_floorplan.id
            ),
            Resource(
                name='Conference Room B',
                type='room',
                x_coordinate=350,
                y_coordinate=100,
                floorplan_id=sample_floorplan.id
            ),
            Resource(
                name='Printer 1',
                type='printer',
                x_coordinate=200,
                y_coordinate=250,
                floorplan_id=sample_floorplan.id
            ),
        ]
        for resource in resources:
            db.session.add(resource)
        db.session.commit()

    return None  # Just need the data to be in the database

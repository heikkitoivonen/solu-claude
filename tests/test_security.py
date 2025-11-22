"""
Tests for security features (CSRF protection).
"""
import json
import pytest
from app import create_app, db


@pytest.fixture
def app_with_csrf():
    """Create application with CSRF enabled."""
    import tempfile
    import os

    db_fd, db_path = tempfile.mkstemp()

    config = {
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'TESTING': True,
        'WTF_CSRF_ENABLED': True,  # Enable CSRF for these tests
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
def csrf_client(app_with_csrf):
    """Create test client with CSRF enabled."""
    return app_with_csrf.test_client()


class TestCSRFProtection:
    """Tests for CSRF protection."""

    def test_post_without_csrf_token_fails(self, csrf_client):
        """Test POST request without CSRF token is rejected."""
        response = csrf_client.post(
            '/api/floorplans',
            data=json.dumps({
                'name': 'Test Floor',
                'image_filename': 'test.png'
            }),
            content_type='application/json'
        )
        assert response.status_code == 400
        assert b'CSRF' in response.data

    def test_put_without_csrf_token_fails(self, csrf_client):
        """Test PUT request without CSRF token is rejected."""
        response = csrf_client.put(
            '/api/resources/1',
            data=json.dumps({'name': 'Updated'}),
            content_type='application/json'
        )
        assert response.status_code == 400
        assert b'CSRF' in response.data

    def test_delete_without_csrf_token_fails(self, csrf_client):
        """Test DELETE request without CSRF token is rejected."""
        response = csrf_client.delete('/api/resources/1')
        assert response.status_code == 400
        assert b'CSRF' in response.data

    def test_get_requests_work_without_csrf(self, csrf_client):
        """Test GET requests don't require CSRF token."""
        response = csrf_client.get('/api/resources')
        assert response.status_code == 200

        response = csrf_client.get('/api/floorplans')
        assert response.status_code == 200

        response = csrf_client.get('/api/search?q=test')
        # Will be 404 (no resources) but not CSRF error
        assert response.status_code == 404

    def test_admin_page_includes_csrf_token(self, csrf_client):
        """Test admin page includes CSRF token meta tag."""
        response = csrf_client.get('/admin')
        assert response.status_code == 200
        assert b'csrf-token' in response.data

"""
Tests for API routes and views.
"""

import json
from io import BytesIO


class TestViews:
    """Tests for view routes."""

    def test_index_page(self, client):
        """Test index page loads."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"Office Resource Locator" in response.data

    def test_admin_page(self, client, admin_user):
        """Test admin page loads after login."""
        # Login first
        client.post(
            "/login",
            data={"username": "testadmin", "password": "Admin123!@#"},
        )
        response = client.get("/admin")
        assert response.status_code == 200
        assert b"Admin Panel" in response.data


class TestSearchAPI:
    """Tests for search API endpoint."""

    def test_search_missing_query(self, client):
        """Test search without query parameter."""
        response = client.get("/api/search")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_search_empty_query(self, client):
        """Test search with empty query."""
        response = client.get("/api/search?q=")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_search_no_results(self, client):
        """Test search with no matches."""
        response = client.get("/api/search?q=NonexistentResource")
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data
        assert "NonexistentResource" in data["error"]

    def test_search_single_result(self, client, sample_resource):
        """Test search with single result."""
        response = client.get("/api/search?q=Test Room")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["count"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["resource"]["name"] == "Test Room"
        assert data["results"][0]["floorplan"]["name"] == "Test Floor"

    def test_search_multiple_results(self, client, multiple_resources):
        """Test search with multiple results."""
        response = client.get("/api/search?q=Conference")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["count"] == 2
        assert len(data["results"]) == 2
        names = [r["resource"]["name"] for r in data["results"]]
        assert "Conference Room A" in names
        assert "Conference Room B" in names

    def test_search_case_insensitive(self, client, sample_resource):
        """Test search is case-insensitive."""
        response = client.get("/api/search?q=test room")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["count"] == 1

    def test_search_partial_match(self, client, sample_resource):
        """Test search with partial string match."""
        response = client.get("/api/search?q=Room")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["count"] >= 1


class TestFloorplansAPI:
    """Tests for floorplans API endpoints."""

    def test_get_floorplans_empty(self, client):
        """Test getting floorplans when none exist."""
        response = client.get("/api/floorplans")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_floorplans(self, client, sample_floorplan):
        """Test getting all floorplans."""
        response = client.get("/api/floorplans")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]["name"] == "Test Floor"

    def test_get_floorplan_by_id(self, client, sample_floorplan):
        """Test getting single floorplan by ID."""
        response = client.get(f"/api/floorplans/{sample_floorplan.id}")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["name"] == "Test Floor"

    def test_get_floorplan_not_found(self, client):
        """Test getting non-existent floorplan."""
        response = client.get("/api/floorplans/999")
        assert response.status_code == 404

    def test_create_floorplan_json(self, client):
        """Test creating floorplan with JSON."""
        response = client.post(
            "/api/floorplans",
            data=json.dumps({"name": "New Floor", "image_filename": "new_floor.png"}),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["name"] == "New Floor"
        assert data["image_filename"] == "new_floor.png"

    def test_create_floorplan_file_upload(self, client):
        """Test creating floorplan with file upload."""
        data = {"name": "Uploaded Floor", "image": (BytesIO(b"fake image data"), "test.png")}
        response = client.post("/api/floorplans", data=data, content_type="multipart/form-data")
        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert response_data["name"] == "Uploaded Floor"
        assert ".png" in response_data["image_filename"]

    def test_create_floorplan_invalid_file_type(self, client):
        """Test creating floorplan with invalid file type."""
        data = {"name": "Bad Floor", "image": (BytesIO(b"fake data"), "test.txt")}
        response = client.post("/api/floorplans", data=data, content_type="multipart/form-data")
        assert response.status_code == 400

    def test_update_floorplan(self, client, sample_floorplan):
        """Test updating a floorplan."""
        response = client.put(
            f"/api/floorplans/{sample_floorplan.id}",
            data=json.dumps({"name": "Updated Floor"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["name"] == "Updated Floor"

    def test_delete_floorplan(self, client, sample_floorplan):
        """Test deleting a floorplan."""
        response = client.delete(f"/api/floorplans/{sample_floorplan.id}")
        assert response.status_code == 204

        # Verify it's deleted
        response = client.get(f"/api/floorplans/{sample_floorplan.id}")
        assert response.status_code == 404


class TestResourcesAPI:
    """Tests for resources API endpoints."""

    def test_get_resources_empty(self, client):
        """Test getting resources when none exist."""
        response = client.get("/api/resources")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_resources(self, client, sample_resource):
        """Test getting all resources."""
        response = client.get("/api/resources")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]["name"] == "Test Room"

    def test_get_resource_by_id(self, client, sample_resource):
        """Test getting single resource by ID."""
        response = client.get(f"/api/resources/{sample_resource.id}")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["name"] == "Test Room"

    def test_get_resource_not_found(self, client):
        """Test getting non-existent resource."""
        response = client.get("/api/resources/999")
        assert response.status_code == 404

    def test_create_resource(self, client, sample_floorplan):
        """Test creating a resource."""
        response = client.post(
            "/api/resources",
            data=json.dumps(
                {
                    "name": "New Printer",
                    "type": "printer",
                    "x_coordinate": 300,
                    "y_coordinate": 400,
                    "floorplan_id": sample_floorplan.id,
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["name"] == "New Printer"
        assert data["type"] == "printer"
        assert data["x_coordinate"] == 300
        assert data["y_coordinate"] == 400

    def test_update_resource(self, client, sample_resource):
        """Test updating a resource."""
        response = client.put(
            f"/api/resources/{sample_resource.id}",
            data=json.dumps({"name": "Updated Room", "x_coordinate": 150}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["name"] == "Updated Room"
        assert data["x_coordinate"] == 150

    def test_delete_resource(self, client, sample_resource):
        """Test deleting a resource."""
        response = client.delete(f"/api/resources/{sample_resource.id}")
        assert response.status_code == 204

        # Verify it's deleted
        response = client.get(f"/api/resources/{sample_resource.id}")
        assert response.status_code == 404

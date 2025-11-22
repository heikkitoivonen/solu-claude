# Office Resource Locator

A Flask web application for locating office resources (people, printers, rooms, etc.) on interactive floorplans. Perfect for small organizations that need a simple way to help employees find resources within their office space.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.14+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.1+-green.svg)

## Features

### For Users
- **Search Interface**: Modern, intuitive web UI for searching resources by name
- **Interactive Floorplans**: View resource locations on visual floorplans with animated cursor
- **Multiple Results**: Smart handling when multiple resources match your search
- **Responsive Design**: Works on desktop and mobile devices

### For Administrators
- **Admin Panel**: Comprehensive management interface at `/admin`
- **Upload Floorplans**: Drag and drop floorplan images (PNG, JPG, SVG, etc.)
- **Interactive Resource Placement**: Click on floorplans to set resource coordinates
- **Full CRUD Operations**: Create, read, update, and delete resources and floorplans
- **Real-time Preview**: See resources on floorplans as you place them

### Technical Features
- RESTful JSON API
- CSRF protection for security
- SQLite database with SQLAlchemy ORM
- Database migrations with Flask-Migrate
- Application factory pattern for testability

## Screenshots

### User Search Interface
Search for any resource and see its location on the floorplan with an animated cursor.

### Admin Panel
Upload floorplans, add resources, and manage everything through an intuitive interface.

## Quick Start

### Prerequisites

- Python 3.14 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd office-resource-locator
```

2. **Install dependencies**
```bash
uv sync
```

3. **Initialize the database**
```bash
uv run flask db upgrade
```

4. **Add sample data (optional)**
```bash
uv run python add_test_data.py
```

5. **Run the application**
```bash
uv run python run.py
```

6. **Open your browser**
- User Interface: http://localhost:8000
- Admin Panel: http://localhost:8000/admin

## Project Structure

```
.
├── app/
│   ├── __init__.py           # Application factory with CSRF protection
│   ├── models.py             # Database models (Floorplan, Resource)
│   ├── routes.py             # API routes and view handlers
│   ├── static/
│   │   ├── css/              # Stylesheets for user and admin UIs
│   │   ├── js/               # JavaScript for interactivity
│   │   └── floorplans/       # Uploaded floorplan images
│   └── templates/
│       ├── index.html        # User search interface
│       └── admin.html        # Admin management panel
├── migrations/               # Database migration scripts
├── run.py                    # Application entry point
├── CLAUDE.md                 # Developer documentation
├── LICENSE.txt               # MIT License
└── pyproject.toml           # Project dependencies (uv/pip)
```

## Usage

### For Users

1. Go to http://localhost:8000
2. Enter a search term (e.g., "Conference Room", "John", "Printer")
3. If multiple matches are found, select the one you want
4. View the floorplan with an animated cursor showing the location

### For Administrators

1. Go to http://localhost:8000/admin
2. **Upload a Floorplan:**
   - Enter a name (e.g., "First Floor")
   - Select an image file
   - Click "Upload Floorplan"

3. **Add a Resource:**
   - Select a floorplan from the dropdown
   - Enter resource name and type
   - Click on the floorplan image to set coordinates
   - Click "Create Resource"

4. **Edit a Resource:**
   - Click "Edit" on any resource
   - Update details and click on the floorplan to change position
   - Click "Update Resource"

5. **Delete:**
   - Click "Delete" on any resource or floorplan

## API Endpoints

### Public Endpoints

#### Search
```http
GET /api/search?q=<query>
```
Returns all resources matching the query with their floorplan information.

**Response:**
```json
{
  "count": 2,
  "results": [
    {
      "resource": {
        "id": 1,
        "name": "Conference Room A",
        "type": "room",
        "x_coordinate": 150,
        "y_coordinate": 100,
        "floorplan_id": 1
      },
      "floorplan": {
        "id": 1,
        "name": "First Floor",
        "image_filename": "floor1.png"
      }
    }
  ]
}
```

### Admin Endpoints (CSRF Protected)

All POST/PUT/DELETE operations require a valid CSRF token.

#### Floorplans
- `GET /api/floorplans` - List all floorplans
- `POST /api/floorplans` - Upload a new floorplan (multipart/form-data)
- `GET /api/floorplans/<id>` - Get floorplan details
- `PUT /api/floorplans/<id>` - Update floorplan
- `DELETE /api/floorplans/<id>` - Delete floorplan (cascades to resources)

#### Resources
- `GET /api/resources` - List all resources
- `POST /api/resources` - Create a new resource
- `GET /api/resources/<id>` - Get resource details
- `PUT /api/resources/<id>` - Update resource
- `DELETE /api/resources/<id>` - Delete resource

## Configuration

Edit `app/__init__.py` to configure:

```python
# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

# Security (change in production!)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'

# CSRF
app.config['WTF_CSRF_TIME_LIMIT'] = None
```

## Database Management

### Using uv (recommended)

```bash
# Create a new migration after model changes
uv run flask db migrate -m "Description of changes"

# Apply migrations
uv run flask db upgrade

# Rollback
uv run flask db downgrade

# Show current version
uv run flask db current
```

### Using pip

```bash
# Install dependencies
pip install -r requirements.txt

# Run migration commands
flask db migrate -m "Description"
flask db upgrade
```

## Security

- **CSRF Protection**: All state-changing operations require valid CSRF tokens
- **Secret Key**: Change `SECRET_KEY` in production
- **File Uploads**: Validates file extensions for uploaded floorplans
- **Secure Filenames**: Uses `secure_filename()` for uploaded files

## Development

See [CLAUDE.md](CLAUDE.md) for detailed developer documentation, including:
- Application architecture
- Database schema
- Common commands
- API endpoint details

## Testing

The application includes comprehensive unit tests with pytest.

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_models.py

# Run specific test class
uv run pytest tests/test_routes.py::TestSearchAPI

# Run with coverage report
uv run pytest --cov=app --cov-report=term-missing
```

### Test Structure

```
tests/
├── conftest.py          # Pytest fixtures and configuration
├── test_models.py       # Database model tests
├── test_routes.py       # API endpoint tests
└── test_security.py     # CSRF protection tests
```

### Test Coverage

Current test coverage: **97%**

The test suite includes:
- **Model Tests**: Database operations, relationships, cascade deletes
- **Route Tests**: All API endpoints, CRUD operations, file uploads
- **Security Tests**: CSRF protection validation
- **Integration Tests**: End-to-end workflows

### Writing New Tests

Tests use pytest fixtures defined in `conftest.py`:
- `app` - Flask application instance with test database
- `client` - Test client for making requests
- `sample_floorplan` - Pre-created floorplan for testing
- `sample_resource` - Pre-created resource for testing
- `multiple_resources` - Multiple resources for search testing

Example test:
```python
def test_search_resource(client, sample_resource):
    """Test searching for a resource."""
    response = client.get('/api/search?q=Test Room')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['count'] == 1
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details.

## Acknowledgments

- Built with Flask, SQLAlchemy, and Flask-WTF
- UI inspired by modern web design patterns
- Created to solve real office navigation challenges

## Support

If you encounter any issues or have questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review the documentation in [CLAUDE.md](CLAUDE.md)

---

Made with ❤️ for small organizations everywhere

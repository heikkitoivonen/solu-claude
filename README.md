# Office Resource Locator

A Flask web application for locating office resources (people, printers, rooms, etc.) on interactive floorplans. Perfect for small organizations that need a simple way to help employees find resources within their office space.

## Features

- **Search for Resources**: Find people, printers, rooms, and other office resources by name
- **Interactive Floorplans**: View resources on visual floorplans with coordinate-based positioning
- **Admin Management**: Add/delete floorplans and manage resources
- **RESTful API**: Clean JSON API for easy integration
- Flask application with factory pattern
- SQLite database backend
- SQLAlchemy ORM for database operations
- Flask-Migrate for automatic schema migrations

## Project Structure

```
.
├── app/
│   ├── __init__.py       # Application factory
│   ├── models.py         # Database models
│   └── routes.py         # API routes
├── run.py                # Application entry point
└── requirements.txt      # Python dependencies
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Initialize Database Migrations

```bash
flask db init
```

This creates a `migrations` directory that tracks your database schema.

### 3. Create Initial Migration

```bash
flask db migrate -m "Initial migration"
```

This generates a migration script based on your models.

### 4. Apply Migration

```bash
flask db upgrade
```

This creates the database tables.

### 5. Run the Application

```bash
python run.py
```

The application will be available at `http://localhost:5000`

## Database Schema Changes

When you modify your models (add/remove fields, create new models, etc.):

```bash
# Generate migration
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade
```

Flask-Migrate automatically detects changes and generates the necessary migration scripts.

## API Endpoints

### Search (Public)

- `GET /api/search?q=<query>` - Search for a resource by name
  - Returns the resource details and its floorplan information
  - Returns 404 with friendly error message if not found

### Floorplans (Admin)

- `GET /api/floorplans` - List all floorplans
- `POST /api/floorplans` - Create a new floorplan
  ```json
  {
    "name": "First Floor",
    "image_filename": "floor1.png"
  }
  ```
- `GET /api/floorplans/<id>` - Get floorplan details
- `PUT /api/floorplans/<id>` - Update floorplan
- `DELETE /api/floorplans/<id>` - Delete floorplan

### Resources (Admin)

- `GET /api/resources` - List all resources
- `POST /api/resources` - Create a new resource
  ```json
  {
    "name": "John Doe",
    "type": "person",
    "x_coordinate": 250,
    "y_coordinate": 180,
    "floorplan_id": 1
  }
  ```
- `GET /api/resources/<id>` - Get resource details
- `PUT /api/resources/<id>` - Update resource
- `DELETE /api/resources/<id>` - Delete resource

## Example Usage

```bash
# Create a floorplan
curl -X POST http://localhost:5000/api/floorplans \
  -H "Content-Type: application/json" \
  -d '{"name": "First Floor", "image_filename": "floor1.png"}'

# Add a resource (person)
curl -X POST http://localhost:5000/api/resources \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "type": "person", "x_coordinate": 250, "y_coordinate": 180, "floorplan_id": 1}'

# Add a resource (printer)
curl -X POST http://localhost:5000/api/resources \
  -H "Content-Type: application/json" \
  -d '{"name": "Color Printer", "type": "printer", "x_coordinate": 400, "y_coordinate": 300, "floorplan_id": 1}'

# Search for a resource
curl http://localhost:5000/api/search?q=John

# List all floorplans
curl http://localhost:5000/api/floorplans

# List all resources
curl http://localhost:5000/api/resources
```

## Configuration

The application can be configured in `app/__init__.py`:

- `SQLALCHEMY_DATABASE_URI` - Database connection string (default: `sqlite:///app.db`)
- `SECRET_KEY` - Secret key for sessions (change in production)
- `SQLALCHEMY_TRACK_MODIFICATIONS` - Disable modification tracking for performance

## Migration Management Commands

```bash
# Show current migration version
flask db current

# Show migration history
flask db history

# Rollback to previous version
flask db downgrade

# Upgrade to specific version
flask db upgrade <revision>
```

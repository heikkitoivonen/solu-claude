# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Application Purpose

This is an **office resource locator** for small organizations. The application allows:
- **Admin users**: Add/delete floorplan images and manage resources (rooms, printers, people, etc.)
- **Regular users**: Search for resources by name, view the relevant floorplan, and see an animated cursor showing the resource's location
- Display friendly error messages when resources are not found

## Application Architecture

This is a Flask web application using the **application factory pattern**. The app is created via `create_app()` in `app/__init__.py`, which:
- Initializes Flask extensions (SQLAlchemy, Flask-Migrate)
- Registers blueprints (currently just the `main` blueprint from `routes.py`)
- Accepts optional config dict for testing/custom configurations

The application structure is:
- `run.py` - Entry point that creates app instance and runs development server
- `app/__init__.py` - Application factory, extension initialization, and blueprint registration
- `app/models.py` - SQLAlchemy models (currently User/Post as starter code; needs to be updated for Floorplan/Resource models)
- `app/routes.py` - All API routes defined in a single Blueprint named `main`

## Database Architecture

- **ORM**: SQLAlchemy with Flask-SQLAlchemy
- **Migrations**: Flask-Migrate handles schema versioning
- **Database**: SQLite (file: `app.db`)

**Current Models** (starter code):
- User (one-to-many with Post)
- Post (belongs to User)

**Intended Models** (for office resource locator):
- Floorplan: Stores floorplan images and metadata
- Resource: Stores searchable resources (rooms, printers, people, etc.) with x/y coordinates on floorplans
- User: For admin authentication and permissions

All models should include `to_dict()` methods for JSON serialization.

## Common Commands

### Running the Application
```bash
python run.py
```
Application runs on `http://localhost:5000` with debug mode enabled.

### Database Migrations

**Initial setup** (only once):
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

**After modifying models**:
```bash
flask db migrate -m "Description of changes"
flask db upgrade
```

**Other migration commands**:
```bash
flask db current    # Show current version
flask db history    # Show all migrations
flask db downgrade  # Rollback one version
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

## API Endpoints

All endpoints are RESTful and return JSON.

**Current Endpoints** (starter code):
- Users: `/api/users` (GET, POST), `/api/users/<id>` (GET, PUT, DELETE)
- Posts: `/api/posts` (GET, POST), `/api/posts/<id>` (GET, PUT, DELETE)
- Root: `/` returns welcome message with endpoint listing

**Intended Endpoints** (for office resource locator):
- Search: `/api/search?q=<query>` - Search for resources by name, returns matching resource with floorplan info
- Floorplans (admin): `/api/floorplans` (GET, POST), `/api/floorplans/<id>` (GET, PUT, DELETE) - Manage floorplan images
- Resources (admin): `/api/resources` (GET, POST), `/api/resources/<id>` (GET, PUT, DELETE) - Manage resources with x/y coordinates
- Authentication: Endpoints for admin login/logout

# CLAUDE.md

<!--
IMPORTANT: Keep this file up to date with all features, architecture changes, and project structure updates.
Last updated: 2024-11 with authentication system, comprehensive security features, and environment configuration.
-->

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Application Purpose

This is an **office resource locator** for small organizations. The application allows:
- **Admin users**: Add/delete floorplan images and manage resources (rooms, printers, people, etc.)
- **Regular users**: Search for resources by name, view the relevant floorplan, and see an animated cursor showing the resource's location
- Display friendly error messages when resources are not found

## Application Architecture

This is a Flask web application using the **application factory pattern**. The app is created via `create_app()` in `app/__init__.py`, which:
- Initializes Flask extensions (SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF)
- Registers blueprints (`main` from `routes.py` and `auth` from `auth_routes.py`)
- Configures security settings (CSRF protection, session cookies, file upload limits)
- Accepts optional config dict for testing/custom configurations

The application structure is:
- `run.py` - Entry point that creates app instance and runs development server (with environment-based debug mode)
- `app/__init__.py` - Application factory, extension initialization, security configuration, and blueprint registration
- `app/models.py` - SQLAlchemy models (User, Floorplan, Resource) with timezone-aware timestamps
- `app/routes.py` - Main API routes (search, floorplans, resources) in the `main` Blueprint
- `app/auth_routes.py` - Authentication routes (login, logout, password management, user management) in the `auth` Blueprint
- `app/templates/` - Jinja2 templates using template inheritance with `base.html`
- `app/static/` - CSS and JavaScript with XSS protection

## Database Architecture

- **ORM**: SQLAlchemy with Flask-SQLAlchemy
- **Migrations**: Flask-Migrate handles schema versioning (timestamp-based filenames)
- **Database**: SQLite (file: `app.db`)

**Models**:

1. **User** - Admin authentication and user management
   - Fields: username, email, password_hash, is_admin, password_must_change, created_at
   - Uses Flask-Login's UserMixin for authentication
   - Password hashing with werkzeug's generate_password_hash
   - Methods: set_password(), check_password(), to_dict()

2. **Floorplan** - Stores floorplan images and metadata
   - Fields: name, image_filename, created_at
   - One-to-many relationship with Resource (cascade delete)
   - Methods: to_dict()

3. **Resource** - Searchable resources with coordinates on floorplans
   - Fields: name, type, x_coordinate, y_coordinate, floorplan_id, created_at
   - Belongs to Floorplan (foreign key)
   - Resource types: room, printer, person, bathroom
   - Type-specific metadata fields:
     - Room: room_number, room_type (meeting/individual), capacity
     - Printer: printer_name, color_type (color/bw), printer_model
     - Person: email, title
     - Bathroom: gender_type (men/women/unisex)
   - Methods: to_dict() (returns type-specific fields)

**Key Features**:
- All models include `to_dict()` methods for JSON serialization
- Timezone-aware timestamps using `datetime.now(timezone.utc)`
- Cascade deletes: Deleting a floorplan also deletes its resources

## Common Commands

**Note**: This project uses `uv` for dependency management. Do NOT use `pip` - use `uv` commands instead.

### Running the Application
```bash
uv run python run.py
```
Application runs on `http://127.0.0.1:8000`. Debug mode is controlled by the `FLASK_DEBUG` environment variable (set to `true` for debug mode).

### Managing Dependencies

**Sync dependencies** (install all dependencies from lockfile):
```bash
uv sync
```

**Add a new dependency**:
```bash
uv add <package-name>
```

**Run any Python command** (automatically uses virtual environment):
```bash
uv run <command>
```

**IMPORTANT: Maintaining pip requirements files**

After adding or updating dependencies in `pyproject.toml`, you MUST regenerate the requirements files for pip users:

```bash
# Regenerate production requirements
uv pip compile pyproject.toml -o requirements.txt

# Regenerate dev requirements (includes testing, linting, etc.)
uv pip compile pyproject.toml --group dev -o requirements-dev.txt
```

This ensures pip users have up-to-date, pinned dependencies that match the uv lockfile. The requirements files include dependency trees showing why each package is installed, which aids in troubleshooting and security audits.

### Database Migrations

**Initial setup** (only once):
```bash
uv run flask db init
uv run flask db migrate -m "Initial migration"
uv run flask db upgrade
```

**After modifying models**:
```bash
uv run flask db migrate -m "Description of changes"
uv run flask db upgrade
```

**Other migration commands**:
```bash
uv run flask db current    # Show current version
uv run flask db history    # Show all migrations
uv run flask db downgrade  # Rollback one version
```

### Testing

**Run tests**:
```bash
uv run pytest              # Run all tests
uv run pytest -v           # Verbose output
uv run pytest tests/test_models.py  # Run specific file

# Run with coverage report
uv run pytest --cov=app --cov-report=term-missing --cov-report=html --cov-branch
```

**Test coverage**: 81% with branch coverage (89 tests passing)

**IMPORTANT: Test coverage requirement**
- **Minimum test coverage must be 80% or greater**
- Always run tests with `--cov-branch` to include branch coverage
- When adding new code, ensure corresponding tests are added to maintain coverage
- Coverage report shows missing lines and branches in `htmlcov/index.html`

**Test structure**:
- `tests/conftest.py` - Fixtures for app, client, sample data, users
- `tests/test_models.py` - Model tests (Floorplan, Resource, User)
- `tests/test_routes.py` - API endpoint tests
- `tests/test_auth_routes.py` - Authentication route tests (login, logout, password management, user management)
- `tests/test_security.py` - CSRF protection tests

**Branch coverage**: Tests include branch coverage, which measures whether all branches of conditional statements (if/else, try/except, etc.) are tested, not just whether lines are executed. This provides more comprehensive test coverage.

**Important note about fixtures**: Fixtures return simple data objects with IDs (not SQLAlchemy objects) to avoid DetachedInstanceError. Tests must query fresh objects within app context:

```python
def test_something(app, sample_floorplan):
    with app.app_context():
        floorplan = Floorplan.query.get(sample_floorplan.id)
        # Now work with the floorplan object
```

### Linting and Code Quality

**Run linters**:
```bash
# Check code with ruff (linter)
uv run ruff check app/ tests/ run.py

# Auto-fix ruff issues
uv run ruff check --fix app/ tests/ run.py

# Format code with black
uv run black app/ tests/ run.py

# Check code formatting without changing files
uv run black --check app/ tests/ run.py

# Type check with mypy
uv run mypy app/ tests/ run.py

# Run all checks
uv run ruff check app/ tests/ run.py && uv run black --check app/ tests/ run.py && uv run mypy app/
```

**Linting tools**:
- **Ruff**: Fast Python linter (replaces flake8, isort, and more)
- **Black**: Opinionated code formatter
- **Mypy**: Static type checker
- **Type Hints**: All function definitions include type annotations

**Configuration**: All linting tools are configured in `pyproject.toml`

**Type Hints**: The codebase uses comprehensive type hints on all function definitions. When adding new functions, always include parameter and return type annotations.

## Security Features

The application implements comprehensive security measures:

### Authentication & Authorization
- **Flask-Login**: Session-based authentication for admin users
- **Password Requirements**: Minimum 10 characters with uppercase, lowercase, numbers, and special characters
- **Password Validation**: `validate_password()` function in `auth_routes.py` enforces requirements
- **Mandatory Password Change**: New users must change password on first login (`password_must_change` flag)
- **Admin-Only Access**: All management endpoints protected with `@login_required` decorator

### Session Security
- **Secure Cookies**: HttpOnly enabled, Secure in production, SameSite=Lax
- **Session Timeout**: 1-hour lifetime (`PERMANENT_SESSION_LIFETIME`)
- **Environment-Based Secrets**: SECRET_KEY from environment variables (`.env` file)

### Input Validation & Protection
- **CSRF Protection**: Flask-WTF protects all POST/PUT/DELETE operations
- **XSS Protection**: HTML escaping in JavaScript (`escapeHtml()` function in `app.js` and `admin.js`)
- **Open Redirect Protection**: `is_safe_url()` function validates redirect URLs in `auth_routes.py`
- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries

### File Upload Security
- **Content Validation**: `validate_image()` function uses Pillow to verify file content (not just extension)
- **File Size Limits**: 16MB maximum (`MAX_CONTENT_LENGTH`)
- **Allowed Formats**: PNG, JPEG, GIF only (SVG removed to prevent XSS attacks)
- **Secure Filenames**: `secure_filename()` with timestamp prefixes to prevent conflicts and directory traversal

### Additional Security
- **Timezone-Aware Timestamps**: Using `datetime.now(timezone.utc)` prevents timezone manipulation
- **Debug Mode Control**: Environment-based, controlled by `FLASK_DEBUG` variable
- **Rate Limiting**: Not currently implemented (noted as enhancement in security review)

## Environment Configuration

The application uses environment variables for configuration. Create a `.env` file based on `.env.example`:

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here-change-me-in-production
FLASK_ENV=development  # or production
FLASK_DEBUG=true       # Only in development, NEVER in production
```

### Environment Variables

**SECRET_KEY** (required in production):
- Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`
- Used for session encryption and CSRF tokens
- Defaults to development key if not set (insecure!)

**FLASK_ENV**:
- `development` or `production`
- In production mode, secure session cookies are enabled

**FLASK_DEBUG**:
- Set to `true` only in development
- Controlled in `run.py` via `os.environ.get("FLASK_DEBUG", "False").lower() == "true"`
- Never enable in production

## API Endpoints

All endpoints are RESTful and return JSON.

### Public Endpoints

**Views**:
- `/` - User search interface (public)
- `/admin` - Admin panel (requires authentication)
- `/login` - Admin login page

**Search API**:
- `GET /api/search?q=<query>` - Search for resources by name, returns matching resources with floorplan info (public)

### Admin Endpoints (Authentication Required)

All floorplan and resource API endpoints require authentication via Flask-Login. POST/PUT/DELETE operations also require valid CSRF tokens.

**Authentication** (`auth` blueprint):
- `POST /login` - Admin login
- `GET /logout` - Logout (requires authentication)
- `GET /change-password` - Password change form (requires authentication)
- `POST /change-password` - Update password (requires authentication)
- `GET /admin/users` - List admin users (requires authentication)
- `POST /admin/users/create` - Create new admin user (requires authentication)
- `POST /admin/users/<id>/delete` - Delete admin user (requires authentication)
- `POST /admin/users/<id>/reset-password` - Reset user password (requires authentication)

**Floorplans** (`main` blueprint):
- `GET /api/floorplans` - List all floorplans (requires authentication)
- `POST /api/floorplans` - Upload new floorplan with file or JSON (requires authentication, CSRF protected)
  - Supports multipart/form-data for file uploads (validates image content with Pillow)
  - Max file size: 16MB
  - Allowed formats: PNG, JPEG, GIF (SVG removed for security)
- `GET /api/floorplans/<id>` - Get floorplan details (requires authentication)
- `PUT /api/floorplans/<id>` - Update floorplan (requires authentication, CSRF protected)
- `DELETE /api/floorplans/<id>` - Delete floorplan (cascades to resources) (requires authentication, CSRF protected)

**Resources** (`main` blueprint):
- `GET /api/resources` - List all resources (requires authentication)
- `POST /api/resources` - Create new resource with type-specific metadata (requires authentication, CSRF protected)
- `GET /api/resources/<id>` - Get resource details (requires authentication)
- `PUT /api/resources/<id>` - Update resource (requires authentication, CSRF protected)
- `DELETE /api/resources/<id>` - Delete resource (requires authentication, CSRF protected)

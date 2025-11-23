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

**Note**: This project uses `uv` for dependency management. Do NOT use `pip` - use `uv` commands instead.

### Running the Application
```bash
uv run python run.py
```
Application runs on `http://localhost:8000` with debug mode enabled.

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

**Test coverage**: 82% with branch coverage (89 tests passing)

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

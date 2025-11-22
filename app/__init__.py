from typing import Any

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()


def create_app(config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)

    # Default configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "dev-secret-key-change-in-production"
    app.config["WTF_CSRF_TIME_LIMIT"] = None  # No time limit for CSRF tokens

    # Override with custom config if provided
    if config:
        app.config.update(config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "main.login"
    login_manager.login_message = "Please log in to access this page."

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id: str) -> Any:
        from app.models import User

        return User.query.get(int(user_id))

    # Register blueprints
    from app.auth_routes import auth
    from app.routes import main

    app.register_blueprint(main)
    app.register_blueprint(auth)

    return app


def create_default_admin() -> None:
    """Create default admin user if it doesn't exist. Call after migrations."""
    from app.models import User

    try:
        # Only create if no admin users exist
        if not User.query.filter_by(username="admin").first():
            admin = User(username="admin", is_admin=True, password_must_change=True)
            admin.set_password("admin")
            db.session.add(admin)
            db.session.commit()
    except Exception:
        # Database table might not exist yet
        pass

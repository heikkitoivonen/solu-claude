"""Authentication routes for user login, logout, and password management."""

from flask import Blueprint, Response, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app import db
from app.models import User

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login() -> str | Response:
    """User login page."""
    if current_user.is_authenticated:
        if current_user.password_must_change:
            return redirect(url_for("auth.change_password"))
        return redirect(url_for("main.admin"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("Username and password are required", "error")
            return render_template("login.html")

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            if not user.is_admin:
                flash("Access denied. Admin privileges required.", "error")
                return render_template("login.html")

            login_user(user)

            if user.password_must_change:
                flash("You must change your password before continuing", "warning")
                return redirect(url_for("auth.change_password"))

            next_page = request.args.get("next")
            return redirect(next_page if next_page else url_for("main.admin"))
        else:
            flash("Invalid username or password", "error")

    return render_template("login.html")


@auth.route("/logout")
@login_required
def logout() -> Response:
    """Log out current user."""
    logout_user()
    flash("You have been logged out successfully", "success")
    return redirect(url_for("main.index"))


@auth.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password() -> str | Response:
    """Change current user's password."""
    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if not all([current_password, new_password, confirm_password]):
            flash("All fields are required", "error")
            return render_template(
                "change_password.html", must_change=current_user.password_must_change
            )

        if not current_user.check_password(current_password):
            flash("Current password is incorrect", "error")
            return render_template(
                "change_password.html", must_change=current_user.password_must_change
            )

        if new_password != confirm_password:
            flash("New passwords do not match", "error")
            return render_template(
                "change_password.html", must_change=current_user.password_must_change
            )

        if len(new_password) < 6:
            flash("Password must be at least 6 characters long", "error")
            return render_template(
                "change_password.html", must_change=current_user.password_must_change
            )

        current_user.set_password(new_password)
        current_user.password_must_change = False
        db.session.commit()

        flash("Password changed successfully", "success")
        return redirect(url_for("main.admin"))

    return render_template("change_password.html", must_change=current_user.password_must_change)


@auth.route("/admin/users")
@login_required
def list_users() -> str:
    """List all admin users."""
    if not current_user.is_admin:
        flash("Access denied", "error")
        return redirect(url_for("main.index"))

    users = User.query.filter_by(is_admin=True).all()
    return render_template("manage_users.html", users=users)


@auth.route("/admin/users/create", methods=["POST"])
@login_required
def create_user() -> Response:
    """Create a new admin user."""
    if not current_user.is_admin:
        flash("Access denied", "error")
        return redirect(url_for("main.index"))

    username = request.form.get("username")
    password = request.form.get("password")

    if not username or not password:
        flash("Username and password are required", "error")
        return redirect(url_for("auth.list_users"))

    if User.query.filter_by(username=username).first():
        flash(f"User '{username}' already exists", "error")
        return redirect(url_for("auth.list_users"))

    user = User(username=username, is_admin=True, password_must_change=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    flash(f"Admin user '{username}' created successfully", "success")
    return redirect(url_for("auth.list_users"))


@auth.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@login_required
def delete_user(user_id: int) -> Response:
    """Delete an admin user."""
    if not current_user.is_admin:
        flash("Access denied", "error")
        return redirect(url_for("main.index"))

    if user_id == current_user.id:
        flash("You cannot delete yourself", "error")
        return redirect(url_for("auth.list_users"))

    user = User.query.get_or_404(user_id)
    username = user.username
    db.session.delete(user)
    db.session.commit()

    flash(f"Admin user '{username}' deleted successfully", "success")
    return redirect(url_for("auth.list_users"))


@auth.route("/admin/users/<int:user_id>/reset-password", methods=["POST"])
@login_required
def reset_user_password(user_id: int) -> Response:
    """Reset another admin user's password."""
    if not current_user.is_admin:
        flash("Access denied", "error")
        return redirect(url_for("main.index"))

    new_password = request.form.get("new_password")
    if not new_password:
        flash("New password is required", "error")
        return redirect(url_for("auth.list_users"))

    user = User.query.get_or_404(user_id)
    user.set_password(new_password)
    user.password_must_change = True
    db.session.commit()

    flash(f"Password reset for '{user.username}'. They must change it on next login.", "success")
    return redirect(url_for("auth.list_users"))

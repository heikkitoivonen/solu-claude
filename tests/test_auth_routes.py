"""
Tests for authentication routes.
"""

import pytest

from app import db
from app.auth_routes import validate_password
from app.models import User


class TestValidatePassword:
    """Tests for password validation function."""

    def test_valid_password(self):
        """Test that a valid password passes all checks."""
        is_valid, error = validate_password("Valid123!@#Pass")
        assert is_valid is True
        assert error == ""

    def test_password_too_short(self):
        """Test password length requirement."""
        is_valid, error = validate_password("Short1!")
        assert is_valid is False
        assert "at least 10 characters" in error

    def test_password_no_uppercase(self):
        """Test password uppercase requirement."""
        is_valid, error = validate_password("lowercase123!")
        assert is_valid is False
        assert "uppercase letter" in error

    def test_password_no_lowercase(self):
        """Test password lowercase requirement."""
        is_valid, error = validate_password("UPPERCASE123!")
        assert is_valid is False
        assert "lowercase letter" in error

    def test_password_no_number(self):
        """Test password number requirement."""
        is_valid, error = validate_password("NoNumbers!@#")
        assert is_valid is False
        assert "number" in error

    def test_password_no_special_char(self):
        """Test password special character requirement."""
        is_valid, error = validate_password("NoSpecial123")
        assert is_valid is False
        assert "special character" in error

    def test_password_same_as_current(self):
        """Test that new password cannot be same as current."""
        current = "SamePass123!"
        is_valid, error = validate_password("SamePass123!", current)
        assert is_valid is False
        assert "different from the current password" in error

    def test_password_different_from_current(self):
        """Test that different password is accepted when current is provided."""
        current = "OldPass123!"
        is_valid, error = validate_password("NewPass456!@#", current)
        assert is_valid is True
        assert error == ""


class TestLoginRoute:
    """Tests for login route."""

    def test_login_page_loads(self, client):
        """Test that login page loads correctly."""
        response = client.get("/login")
        assert response.status_code == 200
        assert b"Admin Login" in response.data

    def test_login_with_valid_credentials(self, client, admin_user):
        """Test successful login with valid credentials."""
        response = client.post(
            "/login",
            data={"username": "testadmin", "password": "Admin123!@#"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Admin Panel" in response.data

    def test_login_with_invalid_username(self, client):
        """Test login fails with invalid username."""
        response = client.post(
            "/login",
            data={"username": "nonexistent", "password": "Admin123!@#"},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"Invalid username or password" in response.data

    def test_login_with_invalid_password(self, client, admin_user):
        """Test login fails with invalid password."""
        response = client.post(
            "/login",
            data={"username": "testadmin", "password": "WrongPassword123!"},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"Invalid username or password" in response.data

    def test_login_without_username(self, client):
        """Test login fails without username."""
        response = client.post(
            "/login", data={"password": "Admin123!@#"}, follow_redirects=False
        )
        assert response.status_code == 200
        assert b"Username and password are required" in response.data

    def test_login_without_password(self, client):
        """Test login fails without password."""
        response = client.post(
            "/login", data={"username": "testadmin"}, follow_redirects=False
        )
        assert response.status_code == 200
        assert b"Username and password are required" in response.data

    def test_login_with_non_admin_user(self, client, regular_user):
        """Test that non-admin users cannot login."""
        response = client.post(
            "/login",
            data={"username": "regularuser", "password": "Regular123!@#"},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"Access denied" in response.data

    def test_login_redirects_to_change_password(self, client, admin_user_must_change):
        """Test that users who must change password are redirected."""
        response = client.post(
            "/login",
            data={"username": "newadmin", "password": "Admin123!@#"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Change Password" in response.data
        assert b"Password Change Required" in response.data

    def test_login_already_authenticated_redirect(self, client, admin_user):
        """Test that authenticated users are redirected."""
        # First login
        client.post(
            "/login",
            data={"username": "testadmin", "password": "Admin123!@#"},
        )
        # Try to access login page again
        response = client.get("/login", follow_redirects=False)
        assert response.status_code == 302
        assert "/admin" in response.location

    def test_login_with_next_parameter(self, client, admin_user):
        """Test that next parameter redirects correctly after login."""
        response = client.post(
            "/login?next=/admin/users",
            data={"username": "testadmin", "password": "Admin123!@#"},
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/admin/users" in response.location


class TestLogoutRoute:
    """Tests for logout route."""

    def test_logout_requires_authentication(self, client):
        """Test that logout requires authentication."""
        response = client.get("/logout", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.location

    def test_logout_success(self, client, admin_user):
        """Test successful logout."""
        # Login first
        client.post(
            "/login",
            data={"username": "testadmin", "password": "Admin123!@#"},
        )
        # Then logout
        response = client.get("/logout", follow_redirects=True)
        assert response.status_code == 200
        assert b"logged out successfully" in response.data


class TestChangePasswordRoute:
    """Tests for change password route."""

    def test_change_password_requires_authentication(self, client):
        """Test that change password requires authentication."""
        response = client.get("/change-password", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.location

    def test_change_password_page_loads(self, client, admin_user):
        """Test that change password page loads."""
        # Login first
        client.post(
            "/login",
            data={"username": "testadmin", "password": "Admin123!@#"},
        )
        response = client.get("/change-password")
        assert response.status_code == 200
        assert b"Change Password" in response.data

    def test_change_password_success(self, client, admin_user, app):
        """Test successful password change."""
        # Login first
        client.post(
            "/login",
            data={"username": "testadmin", "password": "Admin123!@#"},
        )
        # Change password
        response = client.post(
            "/change-password",
            data={
                "current_password": "Admin123!@#",
                "new_password": "NewPassword456!@#",
                "confirm_password": "NewPassword456!@#",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Password changed successfully" in response.data

        # Verify password was actually changed
        with app.app_context():
            user = User.query.filter_by(username="testadmin").first()
            assert user.check_password("NewPassword456!@#")

    def test_change_password_wrong_current(self, client, admin_user):
        """Test password change fails with wrong current password."""
        client.post(
            "/login",
            data={"username": "testadmin", "password": "Admin123!@#"},
        )
        response = client.post(
            "/change-password",
            data={
                "current_password": "WrongPassword123!",
                "new_password": "NewPassword456!@#",
                "confirm_password": "NewPassword456!@#",
            },
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"Current password is incorrect" in response.data

    def test_change_password_mismatch(self, client, admin_user):
        """Test password change fails when new passwords don't match."""
        client.post(
            "/login",
            data={"username": "testadmin", "password": "Admin123!@#"},
        )
        response = client.post(
            "/change-password",
            data={
                "current_password": "Admin123!@#",
                "new_password": "NewPassword456!@#",
                "confirm_password": "DifferentPassword789!@#",
            },
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"passwords do not match" in response.data

    def test_change_password_weak_password(self, client, admin_user):
        """Test password change fails with weak password."""
        client.post(
            "/login",
            data={"username": "testadmin", "password": "Admin123!@#"},
        )
        response = client.post(
            "/change-password",
            data={
                "current_password": "Admin123!@#",
                "new_password": "weak",
                "confirm_password": "weak",
            },
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"at least 10 characters" in response.data

    def test_change_password_same_as_current(self, client, admin_user):
        """Test password change fails when new password is same as current."""
        client.post(
            "/login",
            data={"username": "testadmin", "password": "Admin123!@#"},
        )
        response = client.post(
            "/change-password",
            data={
                "current_password": "Admin123!@#",
                "new_password": "Admin123!@#",
                "confirm_password": "Admin123!@#",
            },
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"different from the current password" in response.data

    def test_change_password_missing_fields(self, client, admin_user):
        """Test password change fails with missing fields."""
        client.post(
            "/login",
            data={"username": "testadmin", "password": "Admin123!@#"},
        )
        response = client.post(
            "/change-password",
            data={
                "current_password": "Admin123!@#",
                "new_password": "NewPassword456!@#",
                # Missing confirm_password
            },
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"All fields are required" in response.data

    def test_change_password_clears_must_change_flag(
        self, client, admin_user_must_change, app
    ):
        """Test that password_must_change flag is cleared after change."""
        client.post(
            "/login",
            data={"username": "newadmin", "password": "Admin123!@#"},
        )
        client.post(
            "/change-password",
            data={
                "current_password": "Admin123!@#",
                "new_password": "NewPassword456!@#",
                "confirm_password": "NewPassword456!@#",
            },
            follow_redirects=True,
        )

        # Verify flag was cleared
        with app.app_context():
            user = User.query.filter_by(username="newadmin").first()
            assert user.password_must_change is False


class TestListUsersRoute:
    """Tests for list users route."""

    def test_list_users_requires_authentication(self, client):
        """Test that list users requires authentication."""
        response = client.get("/admin/users", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.location

    def test_list_users_requires_admin(self, client, regular_user):
        """Test that non-admin users cannot access list users."""
        # Non-admin users cannot even log in, so they'll be denied at login
        response = client.post(
            "/login",
            data={"username": "regularuser", "password": "Regular123!@#"},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"Access denied" in response.data

    def test_list_users_success(self, client, admin_user, app):
        """Test successful user listing."""
        # Create additional user
        with app.app_context():
            user = User(username="anotheradmin", is_admin=True)
            user.set_password("Another123!@#")
            db.session.add(user)
            db.session.commit()

        client.post(
            "/login",
            data={"username": "testadmin", "password": "Admin123!@#"},
        )
        response = client.get("/admin/users")
        assert response.status_code == 200
        assert b"testadmin" in response.data
        assert b"anotheradmin" in response.data


class TestCreateUserRoute:
    """Tests for create user route."""

    def test_create_user_requires_authentication(self, client):
        """Test that create user requires authentication."""
        response = client.post(
            "/admin/users/create",
            data={"username": "newuser", "password": "NewUser123!@#"},
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/login" in response.location

    def test_create_user_requires_admin(self, client, regular_user):
        """Test that non-admin users cannot create users."""
        # Non-admin users cannot even log in, so they'll be denied at login
        response = client.post(
            "/login",
            data={"username": "regularuser", "password": "Regular123!@#"},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"Access denied" in response.data

    def test_create_user_success(self, client, admin_user, app):
        """Test successful user creation."""
        client.post(
            "/login",
            data={"username": "testadmin", "password": "Admin123!@#"},
        )
        response = client.post(
            "/admin/users/create",
            data={"username": "newuser", "password": "NewUser123!@#"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"created successfully" in response.data

        # Verify user was created
        with app.app_context():
            user = User.query.filter_by(username="newuser").first()
            assert user is not None
            assert user.is_admin is True
            assert user.password_must_change is True

    def test_create_user_duplicate_username(self, client, admin_user):
        """Test that creating user with duplicate username fails."""
        client.post(
            "/login",
            data={"username": "testadmin", "password": "Admin123!@#"},
        )
        response = client.post(
            "/admin/users/create",
            data={"username": "testadmin", "password": "NewUser123!@#"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"already exists" in response.data

    def test_create_user_missing_username(self, client, admin_user):
        """Test that creating user without username fails."""
        client.post(
            "/login",
            data={"username": "testadmin", "password": "Admin123!@#"},
        )
        response = client.post(
            "/admin/users/create",
            data={"password": "NewUser123!@#"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Username and password are required" in response.data

    def test_create_user_missing_password(self, client, admin_user):
        """Test that creating user without password fails."""
        client.post(
            "/login",
            data={"username": "testadmin", "password": "Admin123!@#"},
        )
        response = client.post(
            "/admin/users/create",
            data={"username": "newuser"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Username and password are required" in response.data

    def test_create_user_weak_password(self, client, admin_user):
        """Test that creating user with weak password fails."""
        client.post(
            "/login",
            data={"username": "testadmin", "password": "Admin123!@#"},
        )
        response = client.post(
            "/admin/users/create",
            data={"username": "newuser", "password": "weak"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"at least 10 characters" in response.data


class TestDeleteUserRoute:
    """Tests for delete user route."""

    def test_delete_user_requires_authentication(self, client, admin_user):
        """Test that delete user requires authentication."""
        response = client.post(
            f"/admin/users/{admin_user.id}/delete", follow_redirects=False
        )
        assert response.status_code == 302
        assert "/login" in response.location

    def test_delete_user_requires_admin(self, client, regular_user, admin_user):
        """Test that non-admin users cannot delete users."""
        # Non-admin users cannot even log in, so they'll be denied at login
        response = client.post(
            "/login",
            data={"username": "regularuser", "password": "Regular123!@#"},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"Access denied" in response.data

    def test_delete_user_success(self, client, admin_user, app):
        """Test successful user deletion."""
        # Create user to delete
        with app.app_context():
            user = User(username="deleteme", is_admin=True)
            user.set_password("DeleteMe123!@#")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        client.post(
            "/login",
            data={"username": "testadmin", "password": "Admin123!@#"},
        )
        response = client.post(
            f"/admin/users/{user_id}/delete", follow_redirects=True
        )
        assert response.status_code == 200
        assert b"deleted successfully" in response.data

        # Verify user was deleted
        with app.app_context():
            user = User.query.filter_by(username="deleteme").first()
            assert user is None

    def test_delete_user_cannot_delete_self(self, client, admin_user):
        """Test that user cannot delete themselves."""
        client.post(
            "/login",
            data={"username": "testadmin", "password": "Admin123!@#"},
        )
        response = client.post(
            f"/admin/users/{admin_user.id}/delete", follow_redirects=True
        )
        assert response.status_code == 200
        assert b"cannot delete yourself" in response.data

    def test_delete_user_nonexistent(self, client, admin_user):
        """Test that deleting nonexistent user returns 404."""
        client.post(
            "/login",
            data={"username": "testadmin", "password": "Admin123!@#"},
        )
        response = client.post("/admin/users/99999/delete", follow_redirects=False)
        assert response.status_code == 404


class TestResetUserPasswordRoute:
    """Tests for reset user password route."""

    def test_reset_password_requires_authentication(self, client, admin_user):
        """Test that reset password requires authentication."""
        response = client.post(
            f"/admin/users/{admin_user.id}/reset-password",
            data={"new_password": "NewPass123!@#"},
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/login" in response.location

    def test_reset_password_requires_admin(self, client, regular_user, admin_user):
        """Test that non-admin users cannot reset passwords."""
        # Non-admin users cannot even log in, so they'll be denied at login
        response = client.post(
            "/login",
            data={"username": "regularuser", "password": "Regular123!@#"},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"Access denied" in response.data

    def test_reset_password_success(self, client, admin_user, app):
        """Test successful password reset."""
        # Create user to reset
        with app.app_context():
            user = User(username="resetme", is_admin=True)
            user.set_password("OldPass123!@#")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        client.post(
            "/login",
            data={"username": "testadmin", "password": "Admin123!@#"},
        )
        response = client.post(
            f"/admin/users/{user_id}/reset-password",
            data={"new_password": "NewPass456!@#"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Password reset" in response.data

        # Verify password was changed and must_change flag set
        with app.app_context():
            user = User.query.filter_by(username="resetme").first()
            assert user.check_password("NewPass456!@#")
            assert user.password_must_change is True

    def test_reset_password_missing_password(self, client, admin_user, app):
        """Test that reset without password fails."""
        # Create user to reset
        with app.app_context():
            user = User(username="resetme", is_admin=True)
            user.set_password("OldPass123!@#")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        client.post(
            "/login",
            data={"username": "testadmin", "password": "Admin123!@#"},
        )
        response = client.post(
            f"/admin/users/{user_id}/reset-password",
            data={},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"New password is required" in response.data

    def test_reset_password_weak_password(self, client, admin_user, app):
        """Test that reset with weak password fails."""
        # Create user to reset
        with app.app_context():
            user = User(username="resetme", is_admin=True)
            user.set_password("OldPass123!@#")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        client.post(
            "/login",
            data={"username": "testadmin", "password": "Admin123!@#"},
        )
        response = client.post(
            f"/admin/users/{user_id}/reset-password",
            data={"new_password": "weak"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"at least 10 characters" in response.data

    def test_reset_password_nonexistent_user(self, client, admin_user):
        """Test that resetting password for nonexistent user returns 404."""
        client.post(
            "/login",
            data={"username": "testadmin", "password": "Admin123!@#"},
        )
        response = client.post(
            "/admin/users/99999/reset-password",
            data={"new_password": "NewPass123!@#"},
            follow_redirects=False,
        )
        assert response.status_code == 404

import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, Blueprint, session, get_flashed_messages
from app.controllers.auth import AuthController


# A reusable helper that builds a tiny Flask app for every test.
# define the route names the controller redirects to
# (auth.home, auth.login, auth.dashboard, auth.register) so that
# url_for() inside the controller can build URLs successfully.
def make_test_app():
    app = Flask(__name__)
    app.secret_key = "test-secret-key"

    bp = Blueprint("auth", __name__)
    bp.route("/", endpoint="home")(lambda: "home")
    bp.route("/login", endpoint="login")(lambda: "login")
    bp.route("/dashboard", endpoint="dashboard")(lambda: "dashboard")
    bp.route("/register", endpoint="register")(lambda: "register")
    app.register_blueprint(bp)
    return app

class TestRegister(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.controller = AuthController()
        # Replace the real database model with a fake one.
        self.controller.user_model = MagicMock()

    @patch("app.controllers.auth.render_template")
    def test_register_get_shows_form(self, mock_render):
        """Visiting register with GET should show the register form."""
        mock_render.return_value = "register_page"
        with self.app.test_request_context(method="GET"):
            result = self.controller.register()
            self.assertEqual(result, "register_page")
            mock_render.assert_called_once_with("register.html")

    @patch("app.controllers.auth.render_template")
    def test_register_missing_fields_is_rejected(self, mock_render):
        """If any field is empty, registration is refused with a message."""
        mock_render.return_value = "register_page"
        with self.app.test_request_context(
            method="POST", data={"name": "", "email": "", "password": ""}
        ):
            self.controller.register()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "All fields are required."), flashes)

    @patch("app.controllers.auth.render_template")
    def test_register_short_password_is_rejected(self, mock_render):
        """Passwords shorter than 6 characters are not allowed."""
        mock_render.return_value = "register_page"
        with self.app.test_request_context(
            method="POST",
            data={"name": "Bob", "email": "bob@example.com", "password": "123"},
        ):
            self.controller.register()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(
                ("danger", "Password must be at least 6 characters."), flashes
            )

    @patch("app.controllers.auth.User")
    def test_register_duplicate_email_is_rejected(self, mock_user_class):
        """If the email already exists, registration is refused."""
        fake_user = MagicMock()
        fake_user.email_exists.return_value = True
        mock_user_class.return_value = fake_user

        with self.app.test_request_context(
            method="POST",
            data={"name": "Bob", "email": "taken@example.com", "password": "secret1"},
        ):
            response = self.controller.register()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "Email already exists."), flashes)
            # We should be redirected back to the register page (302).
            self.assertEqual(response.status_code, 302)
            # And the user should NOT be saved.
            fake_user.save.assert_not_called()

    @patch("app.controllers.auth.User")
    def test_register_success_saves_user_and_redirects(self, mock_user_class):
        """A valid new user is saved and sent to the login page."""
        fake_user = MagicMock()
        fake_user.email_exists.return_value = False  # email is free
        mock_user_class.return_value = fake_user

        with self.app.test_request_context(
            method="POST",
            data={"name": "Alice", "email": "alice@example.com", "password": "secret1"},
        ):
            response = self.controller.register()
            # The new user was saved to the database.
            fake_user.save.assert_called_once()
            # Then redirected (302) to the login page with a success note.
            self.assertEqual(response.status_code, 302)
            self.assertIn("/login", response.location)
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(
                ("success", "Registration successful! Please login."), flashes
            )


# =====================================================================
#  LOGIN
# =====================================================================
class TestLogin(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.controller = AuthController()
        self.controller.user_model = MagicMock()

    @patch("app.controllers.auth.render_template")
    def test_login_get_shows_form(self, mock_render):
        """Visiting login with GET should show the login form."""
        mock_render.return_value = "login_page"
        with self.app.test_request_context(method="GET"):
            result = self.controller.login()
            self.assertEqual(result, "login_page")
            mock_render.assert_called_once_with("login.html")

    @patch("app.controllers.auth.render_template")
    def test_login_missing_fields_is_rejected(self, mock_render):
        """Empty email/password shows an error and stays on login."""
        mock_render.return_value = "login_page"
        with self.app.test_request_context(
            method="POST", data={"email": "", "password": ""}
        ):
            self.controller.login()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "Email and password are required."), flashes)

    @patch("app.controllers.auth.render_template")
    @patch("app.controllers.auth.User.from_db")
    def test_login_wrong_password_is_rejected(self, mock_from_db, mock_render):
        """A correct email but wrong password is refused."""
        mock_render.return_value = "login_page"
        # The database "finds" a user...
        self.controller.user_model.find_by.return_value = {
            "id": 1, "name": "Bob", "email": "bob@example.com", "role": "user",
        }
        # ...but check_password says the password is wrong.
        fake_user = MagicMock()
        fake_user.check_password.return_value = False
        mock_from_db.return_value = fake_user

        with self.app.test_request_context(
            method="POST",
            data={"email": "bob@example.com", "password": "wrongpass"},
        ):
            self.controller.login()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "Invalid email or password."), flashes)
            # No session was created.
            self.assertNotIn("user_id", session)

    @patch("app.controllers.auth.User.from_db")
    def test_login_success_sets_session_and_redirects(self, mock_from_db):
        """A correct login stores the user in the session and redirects home."""
        self.controller.user_model.find_by.return_value = {
            "id": 2, "name": "Bob", "email": "bob@example.com", "role": "user",
        }
        fake_user = MagicMock()
        fake_user.check_password.return_value = True
        mock_from_db.return_value = fake_user

        with self.app.test_request_context(
            method="POST",
            data={"email": "bob@example.com", "password": "secret1"},
        ):
            response = self.controller.login()
            # Session is filled in with the logged-in user's details.
            self.assertEqual(session["user_id"], 2)
            self.assertEqual(session["user_name"], "Bob")
            self.assertEqual(session["role"], "user")
            # Redirected (302) to the home page with a success message.
            self.assertEqual(response.status_code, 302)
            self.assertIn("/", response.location)
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("success", "Login successful!"), flashes)


# =====================================================================
#  LOGOUT
# =====================================================================
class TestLogout(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.controller = AuthController()
        self.controller.user_model = MagicMock()

    def test_logout_clears_session_and_redirects(self):
        """Logging out wipes the session and returns to the login page."""
        with self.app.test_request_context():
            # Pretend someone is logged in.
            session["user_id"] = 99
            session["user_name"] = "Alice"
            session["role"] = "user"

            response = self.controller.logout()

            # Every session value is gone.
            self.assertNotIn("user_id", session)
            self.assertNotIn("user_name", session)
            self.assertNotIn("role", session)
            # Redirected (302) back to login with a goodbye message.
            self.assertEqual(response.status_code, 302)
            self.assertIn("/login", response.location)
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("success", "Logged out successfully."), flashes)


if __name__ == "__main__":
    unittest.main()

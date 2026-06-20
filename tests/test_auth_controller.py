import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, Blueprint, session, get_flashed_messages, jsonify
from app.controllers.auth_controller import AuthController

def make_test_app():
    app = Flask(__name__)
    app.secret_key = "test-secret-key"

    bp = Blueprint("auth", __name__)
    bp.route("/", endpoint="home")(lambda: "home")
    bp.route("/login", endpoint="login_page")(lambda: "login")
    bp.route("/dashboard", endpoint="dashboard")(lambda: "dashboard")
    bp.route("/signup", endpoint="signup_page")(lambda: "signup")
    app.register_blueprint(bp)
    return app

class TestRegister(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.controller = AuthController()

    @patch("app.controllers.auth_controller.render_template")
    def test_register_get_shows_form(self, mock_render):
        """Visiting register with GET should show the register form."""
        mock_render.return_value = "signup_page"
        with self.app.test_request_context(method="GET"):
            result = self.controller.signup_page()
            self.assertEqual(result, "signup_page")
            mock_render.assert_called_once_with("signup.html")

    def test_register_missing_fields_is_rejected(self):
        """If any field is empty, registration is refused with a message."""
        with self.app.test_request_context(
            method="POST", json={"username": "", "email": "", "password": ""}
        ):
            response, status = self.controller.register()
            self.assertEqual(status, 422)
            self.assertIn("errors", response.json)
            self.assertIn("email", response.json["errors"])

    def test_register_short_password_is_rejected(self):
        """Passwords shorter than 8 characters are not allowed."""
        with self.app.test_request_context(
            method="POST",
            json={
                "username": "bob123", 
                "email": "bob@example.com", 
                "password": "123", 
                "confirm_password": "123", 
                "agreed": True
            },
        ):
            response, status = self.controller.register()
            self.assertEqual(status, 422)
            self.assertIn("errors", response.json)
            self.assertIn("password", response.json["errors"])

    @patch("app.controllers.auth_controller.User")
    def test_register_duplicate_email_is_rejected(self, mock_user_class):
        """If the email already exists, registration is refused."""
        # Mock User().find_by to return a truthy value (existing user)
        mock_user_class.return_value.find_by.return_value = {"id": 1}

        with self.app.test_request_context(
            method="POST",
            json={
                "username": "bob123", 
                "email": "taken@example.com", 
                "password": "password123",
                "confirm_password": "password123",
                "agreed": True
            },
        ):
            response, status = self.controller.register()
            self.assertEqual(status, 422)
            self.assertIn("errors", response.json)
            self.assertIn("email", response.json["errors"])

    @patch("app.controllers.auth_controller.User")
    @patch("app.controllers.auth_controller.EmailVerification")
    def test_register_success_saves_user_and_redirects(self, mock_ev_class, mock_user_class):
        """A valid new user is saved and sent to the home page via JSON redirect."""
        # Return None to simulate email/username not existing
        mock_user_class.return_value.find_by.return_value = None
        mock_user_class.return_value.id = 2
        mock_user_class.return_value.username = "alice123"

        with self.app.test_request_context(
            method="POST",
            json={
                "username": "alice123", 
                "email": "alice@example.com", 
                "password": "password123",
                "confirm_password": "password123",
                "agreed": True
            },
        ):
            response, status = self.controller.register()
            # The new user was saved to the database.
            mock_user_class.return_value.save.assert_called_once()
            # JSON response returned 201 with success
            self.assertEqual(status, 201)
            self.assertTrue(response.json["success"])
            self.assertIn("/", response.json["redirect"])


# =====================================================================
#  LOGIN
# =====================================================================
class TestLogin(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.controller = AuthController()

    @patch("app.controllers.auth_controller.render_template")
    def test_login_get_shows_form(self, mock_render):
        """Visiting login with GET should show the login form."""
        mock_render.return_value = "login_page"
        with self.app.test_request_context(method="GET"):
            result = self.controller.login()
            self.assertEqual(result, "login_page")
            mock_render.assert_called_once_with("login.html")

    def test_login_missing_fields_is_rejected(self):
        """Empty email/password shows an error via JSON API."""
        with self.app.test_request_context(
            method="POST", json={"identifier": "", "password": ""}
        ):
            response, status = self.controller.login()
            self.assertEqual(status, 400)
            self.assertFalse(response.json["success"])
            self.assertEqual(response.json["message"], "All fields are required")

    @patch("app.controllers.auth_controller.User.from_db")
    @patch("app.controllers.auth_controller.User")
    def test_login_wrong_password_is_rejected(self, mock_user_class, mock_from_db):
        """A correct email but wrong password is refused."""
        # The database "finds" a user...
        mock_user_class.return_value.find_by.return_value = {
            "id": 1, "username": "bob123", "email": "bob@example.com"
        }
        # ...but check_password says the password is wrong.
        fake_user = MagicMock()
        fake_user.check_password.return_value = False
        mock_from_db.return_value = fake_user

        with self.app.test_request_context(
            method="POST",
            json={"identifier": "bob@example.com", "password": "wrongpass"},
        ):
            response, status = self.controller.login()
            self.assertEqual(status, 401)
            self.assertFalse(response.json["success"])
            self.assertIn("Invalid username/email or password.", response.json["message"])
            # No session was created.
            self.assertNotIn("user_id", session)

    @patch("app.controllers.auth_controller.User.from_db")
    @patch("app.controllers.auth_controller.User")
    def test_login_success_sets_session_and_redirects(self, mock_user_class, mock_from_db):
        """A correct login stores the user in the session and redirects home via JSON."""
        mock_user_class.return_value.find_by.return_value = {
            "id": 2, "username": "bob123", "email": "bob@example.com"
        }
        fake_user = MagicMock()
        fake_user.id = 2
        fake_user.username = "bob123"
        fake_user.check_password.return_value = True
        mock_from_db.return_value = fake_user

        with self.app.test_request_context(
            method="POST",
            json={"identifier": "bob@example.com", "password": "secret1"},
        ):
            response, status = self.controller.login()
            # Session is filled in with the logged-in user's details.
            self.assertEqual(session["user_id"], 2)
            self.assertEqual(session["username"], "bob123")
            # Returns 200 OK with success JSON
            self.assertEqual(status, 200)
            self.assertTrue(response.json["success"])
            self.assertIn("/", response.json["redirect"])


# =====================================================================
#  LOGOUT
# =====================================================================
class TestLogout(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.controller = AuthController()

    def test_logout_clears_session_and_redirects(self):
        """Logging out wipes the session and returns to the login page."""
        with self.app.test_request_context():
            # Pretend someone is logged in.
            session["user_id"] = 99
            session["username"] = "Alice"

            response = self.controller.logout()

            # Every session value is gone.
            self.assertNotIn("user_id", session)
            self.assertNotIn("username", session)
            # Redirected (302) back to login
            self.assertEqual(response.status_code, 302)
            self.assertIn("/login", response.location)


if __name__ == "__main__":
    unittest.main()

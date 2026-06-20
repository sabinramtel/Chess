import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, Blueprint, session, get_flashed_messages
from app.controllers.auth_controller import AuthController

def make_test_app():
    app = Flask(__name__)
    app.secret_key = "test-secret-key"
    bp = Blueprint("auth", __name__)
    @bp.route("/", endpoint="home")
    def home():
        return "home"
    @bp.route("/login", endpoint="login_page")
    def login():
        return ""
    @bp.route("/verify", endpoint="verify_email_page")
    def verify():
        return ""
    app.register_blueprint(bp)
    return app

class TestRegister(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    @patch("app.controllers.auth_controller.User")
    @patch("app.controllers.auth_controller.db.session")
    def test_register_missing_fields(self, mock_session, mock_user):
        with self.app.test_request_context(method="POST", json={}):
            response, status = AuthController.register()
            self.assertEqual(status, 400)

    @patch("app.controllers.auth_controller.User")
    @patch("app.controllers.auth_controller.db.session")
    def test_register_success(self, mock_session, mock_user):
        mock_user.query.filter_by.return_value.first.return_value = None
        data = {
            "email": "test@test.com",
            "username": "testuser",
            "password": "password123",
            "confirm_password": "password123",
            "agreed": True
        }
        with self.app.test_request_context(method="POST", json=data):
            response, status = AuthController.register()
            self.assertEqual(status, 201)
            self.assertIn("pending_user_id", session)

class TestLogin(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    @patch("app.controllers.auth_controller.render_template")
    def test_login_get(self, mock_render):
        mock_render.return_value = "login_page"
        with self.app.test_request_context(method="GET"):
            result = AuthController.login()
            self.assertEqual(result, "login_page")

    @patch("app.controllers.auth_controller.User")
    def test_login_success(self, mock_user):
        fake_user = MagicMock()
        fake_user.id = 1
        fake_user.username = "testuser"
        fake_user.check_password.return_value = True
        mock_user.query.filter.return_value.first.return_value = fake_user

        with self.app.test_request_context(method="POST", json={"identifier": "testuser", "password": "password123"}):
            response, status = AuthController.login()
            self.assertEqual(status, 200)
            self.assertEqual(session["user_id"], 1)

    @patch("app.controllers.auth_controller.User")
    def test_login_fail(self, mock_user):
        fake_user = MagicMock()
        fake_user.check_password.return_value = False
        mock_user.query.filter.return_value.first.return_value = fake_user

        with self.app.test_request_context(method="POST", json={"identifier": "testuser", "password": "wrong"}):
            response, status = AuthController.login()
            self.assertEqual(status, 401)
            self.assertNotIn("user_id", session)

if __name__ == "__main__":
    unittest.main()

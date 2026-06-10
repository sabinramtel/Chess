from flask import Blueprint
from app.auth import admin_required
from app.controllers.auth import AuthController


class AuthRoutes:
    def __init__(self):
        self.bp = Blueprint("auth", __name__)
        self.controller = AuthController()

    def register(self):
        self.bp.route("/", methods=["GET"])(self.controller.home_page)
        self.bp.route("/signup", methods=["GET"])(self.controller.signup_page)
        self.bp.route("/login", methods=["GET"])(self.controller.login_page)
        self.bp.route("/settings", methods=["GET"])(self.controller.settings_page)
        self.bp.route("/play", methods=["GET"])(self.controller.play_page)
        self.bp.route("/logout", methods=["GET"])(self.controller.logout)

        self.bp.route("/api/health", methods=["GET"])(self.controller.health)
        self.bp.route("/api/check-username", methods=["GET"])(self.controller.check_username)
        self.bp.route("/api/register", methods=["POST"])(self.controller.register)
        self.bp.route("/api/login", methods=["POST"])(self.controller.login)
        self.bp.route("/users/<int:id>/edit", methods=["GET", "POST"])(admin_required(self.controller.editUsers))
        self.bp.route("/users/<int:id>/delete", methods=["GET", "POST"])(admin_required(self.controller.deleteUsers))

        return self.bp

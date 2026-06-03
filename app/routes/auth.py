from flask import Blueprint
from app.controllers.auth import AuthController


class AuthRoutes:
    def __init__(self):
        self.bp = Blueprint("auth", __name__)
        self.controller = AuthController()

    def register(self):
        self.bp.route("/", methods=["GET"])(self.controller.index)
        self.bp.route("/login", methods=["GET"])(self.controller.login_page)

        self.bp.route("/api/health", methods=["GET"])(self.controller.health)
        self.bp.route("/api/check-username", methods=["GET"])(self.controller.check_username)
        self.bp.route("/api/register", methods=["POST"])(self.controller.register)
        self.bp.route("/api/login", methods=["POST"])(self.controller.login)

        return self.bp

from flask import Blueprint
from app.controllers.auth_controller import AuthController
from app.auth import login_required


class AuthRoutes:
    def __init__(self):
        self.bp = Blueprint('auth', __name__)
        self.controller = AuthController()

    def register(self):
        # --- Frontend Page Routes ---

        self.bp.route('/')(
            self.controller.index
        )
        self.bp.route('/home')(
            login_required(self.controller.home)
        )
        self.bp.route('/play')(
            login_required(self.controller.play)
        )
        self.bp.route('/puzzle')(
            login_required(self.controller.puzzle_page)
        )
        self.bp.route('/lobby')(
            login_required(self.controller.lobby)
        )
        self.bp.route('/login', methods=['GET', 'POST'])(
            self.controller.login_page
        )
        self.bp.route('/api/login', methods=['POST'])(
            self.controller.login
        )
        self.bp.route('/logout')(
            self.controller.logout
        )
        self.bp.route('/signup')(
            self.controller.signup_page
        )
        self.bp.route('/forgot-password')(
            self.controller.forgot_password_page
        )
        self.bp.route('/profile/<username>')(
            login_required(self.controller.user_profile)
        )
        self.bp.route('/verify-email')(
            self.controller.verify_email_page
        )
        self.bp.route('/stats')(
            login_required(self.controller.stats_page)
        )
        self.bp.route('/privacy')(
            self.controller.privacy
        )
        self.bp.route('/tos')(
            self.controller.tos
        )

        # --- Backend API Endpoints (For Async Fetch Requests) ---

        self.bp.route('/api/forgot-password', methods=['POST'])(
            self.controller.forgot_password
        )
        self.bp.route('/api/reset-password', methods=['POST'])(
            self.controller.reset_password
        )
        self.bp.route('/api/check-username', methods=['GET'])(
            self.controller.check_username
        )
        self.bp.route('/api/register', methods=['POST'])(
            self.controller.register
        )
        self.bp.route('/api/verify-email', methods=['POST'])(
            self.controller.verify_email
        )
        self.bp.route('/api/resend-otp', methods=['POST'])(
            self.controller.resend_otp
        )
        self.bp.route('/api/quote', methods=['GET'])(
            self.controller.get_quote
        )

        # --- Deployment-specific routes ---

        self.bp.route('/health')(
            self.controller.health
        )
        self.bp.route('/api/db-status')(
            self.controller.db_status
        )

        # TEMPORARY DIAGNOSTIC HANDLER
        self.bp.app_errorhandler(Exception)(
            self.controller.handle_exception
        )

        return self.bp


# Module-level blueprint for backward compatibility with app/__init__.py
auth_bp = AuthRoutes().register()

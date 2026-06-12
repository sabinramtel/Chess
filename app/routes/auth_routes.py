from flask import Blueprint, current_app, send_from_directory

from app.controllers.auth_controller import AuthController
 
auth_bp = Blueprint('auth', __name__)
 
# --- Frontend Page Routes ---
 
@auth_bp.route('/')

def index():

    """Serves the main frontend dashboard/index file."""

    return send_from_directory(current_app.static_folder, 'index.html')
 
 
@auth_bp.route('/login', methods=['GET', 'POST'])

def login_page():

    """Serves the login page (GET) and processes form/API authentication logins (POST)."""

    return AuthController.login()
 
 
# --- Backend API Endpoints (For Async Fetch Requests) ---
 
@auth_bp.route('/api/check-username', methods=['GET'])

def check_username():

    """Endpoint for checking username availability live during registration."""

    return AuthController.check_username()
 
 
@auth_bp.route('/api/register', methods=['POST'])

def register():

    """Endpoint for creating a new user account."""

    return AuthController.register()
 
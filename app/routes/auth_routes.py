from flask import Blueprint, current_app, send_from_directory
from app.controllers.auth_controller import AuthController

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    return send_from_directory(current_app.static_folder, 'index.html')


@auth_bp.route('/api/check-username', methods=['GET'])
def check_username():
    return AuthController.check_username()


@auth_bp.route('/api/register', methods=['POST'])
def register():
    return AuthController.register()

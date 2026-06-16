from flask import Blueprint, render_template, session, redirect, url_for
 
from app.controllers.auth_controller import AuthController
 
auth_bp = Blueprint('auth', __name__)
 
# --- Frontend Page Routes ---
 
@auth_bp.route('/')
def index():
    return render_template('index.html')
 
 
@auth_bp.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    return render_template('home.html',
                           username=session.get('username'),
                           user_id=session.get('user_id'))
 
 
@auth_bp.route('/login', methods=['GET', 'POST'])
def login_page():
    return AuthController.login()
 
 
@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login_page'))
 
 
# --- Backend API Endpoints (For Async Fetch Requests) ---
 
@auth_bp.route('/api/check-username', methods=['GET'])
def check_username():
    return AuthController.check_username()
 
 
@auth_bp.route('/api/register', methods=['POST'])
def register():
    return AuthController.register()
from flask import Blueprint, render_template, session, redirect, url_for
from app.controllers.auth_controller import AuthController

auth_bp = Blueprint('auth', __name__)

# --- Frontend Page Routes ---

@auth_bp.route('/')
def index():
    return render_template('index.html')


@auth_bp.route('/health')
def health():
    return 'OK', 200


@auth_bp.route('/api/db-status')
def db_status():
    """Diagnostic endpoint — shows DB connectivity and which env vars are set."""
    import os, re
    from flask import jsonify
    from sqlalchemy import text
    from app import db

    # Check which Railway/MySQL env vars are present (mask passwords)
    def present(key):
        val = os.environ.get(key)
        if val is None:
            return 'NOT SET'
        if 'password' in key.lower() or 'pass' in key.lower():
            return '*** (set)'
        return val

    env_vars = {
        'DATABASE_URL':  present('DATABASE_URL'),
        'MYSQL_URL':     present('MYSQL_URL'),
        'MYSQLHOST':     present('MYSQLHOST'),
        'MYSQLPORT':     present('MYSQLPORT'),
        'MYSQLUSER':     present('MYSQLUSER'),
        'MYSQLPASSWORD': present('MYSQLPASSWORD'),
        'MYSQLDATABASE': present('MYSQLDATABASE'),
        'MYSQL_HOST':    present('MYSQL_HOST'),
        'MYSQL_USER':    present('MYSQL_USER'),
        'MYSQL_PASSWORD':present('MYSQL_PASSWORD'),
        'MYSQL_DB':      present('MYSQL_DB'),
    }

    # Redact password from configured URI
    from flask import current_app
    raw_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', 'not configured')
    safe_uri = re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', raw_uri)

    try:
        db.session.execute(text('SELECT 1'))
        db.session.rollback()
        db_ok = True
        db_error = None
    except Exception as e:
        db_ok = False
        db_error = str(e)

    return jsonify({
        'db_connected': db_ok,
        'db_error': db_error,
        'configured_uri': safe_uri,
        'env_vars': env_vars,
    })


@auth_bp.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    return render_template('home.html',
                           active_page='home',
                           username=session.get('username'),
                           user_id=session.get('user_id'))


@auth_bp.route('/play')
def play():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    return render_template('play.html',
                           active_page='play',
                           username=session.get('username'),
                           user_id=session.get('user_id'))


@auth_bp.route('/puzzle')
def puzzle_page():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    return render_template('puzzle.html',
                           active_page='puzzle',
                           username=session.get('username'),
                           user_id=session.get('user_id'))


@auth_bp.route('/lobby')
def lobby():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    return render_template('lobby.html',
                           active_page='lobby',
                           username=session.get('username'),
                           user_id=session.get('user_id'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login_page():
    return AuthController.login()


@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    return AuthController.login()


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login_page'))


@auth_bp.route('/tier')
def tier_page():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    return render_template('tier.html',
                           active_page='tier',
                           username=session.get('username'),
                           user_id=session.get('user_id'))


@auth_bp.route('/profile/<username>')
def user_profile(username):
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    return redirect(url_for('auth.home'))


@auth_bp.route('/forgot-password')
def forgot_password_page():
    return render_template('forgot_password.html')


@auth_bp.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    return AuthController.forgot_password()


@auth_bp.route('/api/reset-password', methods=['POST'])
def reset_password():
    return AuthController.reset_password()


# --- Backend API Endpoints (For Async Fetch Requests) ---

@auth_bp.route('/api/check-username', methods=['GET'])
def check_username():
    return AuthController.check_username()


@auth_bp.route('/api/register', methods=['POST'])
def register():
    return AuthController.register()


@auth_bp.route('/verify-email')
def verify_email_page():
    if 'pending_user_id' not in session:
        return redirect(url_for('auth.login_page'))
    return render_template('verify_otp.html')


@auth_bp.route('/api/verify-email', methods=['POST'])
def verify_email():
    return AuthController.verify_email()


@auth_bp.route('/api/resend-otp', methods=['POST'])
def resend_otp():
    return AuthController.resend_otp()

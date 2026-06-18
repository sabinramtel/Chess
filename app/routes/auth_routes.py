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

    from app.models.user import User
    profile_user = User.query.filter_by(username=username).first()
    if not profile_user:
        return redirect(url_for('auth.home'))

    return render_template(
        'profile.html',
        active_page='profile',
        profile_user=profile_user,
        is_own_profile=(session.get('user_id') == profile_user.id),
        games_played=0,
        wins=0,
        losses=0,
        history=[],
        hidden_games=[],
        hidden_count=0,
    )


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

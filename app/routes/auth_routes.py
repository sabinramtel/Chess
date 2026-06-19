from flask import Blueprint, render_template, session, redirect, url_for, abort
from app.controllers.auth_controller import AuthController

auth_bp = Blueprint('auth', __name__)

# --- Frontend Page Routes ---

@auth_bp.route('/')
def index():
    return render_template('index.html')


@auth_bp.route('/health')
def health():
    return 'OK', 200

# TEMPORARY DIAGNOSTIC HANDLER
from flask import current_app, jsonify
import traceback
@auth_bp.app_errorhandler(Exception)
def handle_exception(e):
    # Catch everything and return the traceback
    tb = traceback.format_exc()
    return jsonify({
        "error": "Unhandled Exception",
        "message": str(e),
        "traceback": tb
    }), 500

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
    from app.models.puzzle_stats_model import UserPuzzleStats
    from app.models.settings_model import UserSettings
    from app import db
    user_id = session.get('user_id')
    stats = UserPuzzleStats.query.filter_by(user_id=user_id).first()
    if not stats:
        stats = UserPuzzleStats(user_id=user_id)
        db.session.add(stats)
        db.session.commit()
    user_settings = UserSettings.query.filter_by(user_id=user_id).first()
    avatar_url = user_settings.avatar_url if user_settings and user_settings.avatar_url else None
    return render_template('home.html',
                           active_page='home',
                           username=session.get('username'),
                           user_id=user_id,
                           streak=stats.streak_current,
                           puzzle_rating=stats.puzzle_rating,
                           total_solved=stats.total_solved,
                           avatar_url=avatar_url)


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





@auth_bp.route('/profile/<username>')
def user_profile(username):
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
<<<<<<< HEAD
    return redirect(url_for('auth.home'))
=======

    from app.models.user_model import User
    from app.models.puzzle_stats_model import UserPuzzleStats
    from app.models.settings_model import UserSettings
    user = User.query.filter_by(username=username).first()
    if not user:
        abort(404)

    puzzle_stats = UserPuzzleStats.query.filter_by(user_id=user.id).first()
    user_settings = UserSettings.query.filter_by(user_id=user.id).first()
    avatar_url = user_settings.avatar_url if user_settings and user_settings.avatar_url else None

    return render_template(
        'profile.html',
        active_page='profile',
        profile_user=user,
        profile_username=user.username,
        avatar_url=avatar_url,
        rating=user.rating,
        joined_date=user.created_at.strftime('%B %Y') if user.created_at else None,
        username=session.get('username'),
        user_id=session.get('user_id'),
        is_own_profile=(session.get('user_id') == user.id),
        puzzle_rating=puzzle_stats.puzzle_rating if puzzle_stats else 1200,
        total_solved=puzzle_stats.total_solved if puzzle_stats else 0,
        total_attempted=puzzle_stats.total_attempted if puzzle_stats else 0,
        streak=puzzle_stats.streak_current if puzzle_stats else 0,
        history=[],
        hidden_games=[],
        hidden_count=0,
    )


@auth_bp.route('/signup')
def signup_page():
    return render_template('signup.html')
>>>>>>> origin/main


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

<<<<<<< HEAD

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


@auth_bp.route('/api/quote', methods=['GET'])
def get_quote():
    import requests
    from flask import current_app, jsonify
    api_key = current_app.config.get('GROQ_API_KEY')
    if not api_key:
        return jsonify({'quote': 'Chess is life. - Bobby Fischer (Fallback)'}), 200

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    payload = {
        'model': 'llama-3.1-8b-instant',
        'messages': [{'role': 'user', 'content': 'Give me exactly one very short, inspiring chess quote from a grandmaster. Return ONLY a valid JSON object with exactly two keys: "quote" (the quote text) and "author" (the full standard Wikipedia name of the grandmaster). Do not include any markdown formatting or extra text.'}],
        'max_tokens': 100
    }
    try:
        response = requests.post('https://api.groq.com/openai/v1/chat/completions', headers=headers, json=payload, timeout=5)
        response.raise_for_status()
        data = response.json()
        content = data['choices'][0]['message']['content'].strip()
        import json
        parsed = json.loads(content)
        return jsonify({'quote': parsed.get('quote', ''), 'author': parsed.get('author', '')})
    except Exception as e:
        print(f"Groq API Error: {e}")
        return jsonify({'quote': 'The blunders are all there on the board, waiting to be made.', 'author': 'Savielly Tartakower'}), 200


@auth_bp.route('/privacy')
def privacy():
    return render_template('privacy.html')


@auth_bp.route('/tos')
def tos():
    return render_template('tos.html')
=======
>>>>>>> origin/main

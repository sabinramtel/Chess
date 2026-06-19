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

    from app.models.user_model import User
    from app.models.puzzle_stats_model import UserPuzzleStats
    from app.models.settings_model import UserSettings
    user = User.query.filter_by(username=username).first()
    if not user:
        return render_template('tier.html', active_page='profile'), 404

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


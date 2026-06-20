from flask import Blueprint, render_template, session, redirect, url_for, abort, request, current_app, jsonify
from app.controllers.auth_controller import AuthController
import traceback

auth_bp = Blueprint('auth', __name__)

# --- Frontend Page Routes ---

@auth_bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('auth.home'))
    return render_template('index.html')


@auth_bp.route('/health')
def health():
    return 'OK', 200


# TEMPORARY DIAGNOSTIC HANDLER
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
    if request.method == 'GET' and 'user_id' in session:
        return redirect(url_for('auth.home'))
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
    if 'user_id' in session:
        return redirect(url_for('auth.home'))
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


@auth_bp.route('/stats')
def stats_page():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))

    from app.models.puzzle_stats_model import UserPuzzleStats
    from app.models.settings_model import UserSettings
    from app.models.user_model import User
    from app.models.puzzle_attempt_model import PuzzleAttempt

    user_id = session.get('user_id')
    user = User.query.get(user_id)
    stats = UserPuzzleStats.query.filter_by(user_id=user_id).first()
    user_settings = UserSettings.query.filter_by(user_id=user_id).first()
    avatar_url = user_settings.avatar_url if user_settings and user_settings.avatar_url else None

    recent_attempts = (PuzzleAttempt.query
        .filter_by(user_id=user_id)
        .order_by(PuzzleAttempt.attempted_at.desc())
        .limit(6).all())

    accuracy = round(stats.total_solved / stats.total_attempted * 100) if stats and stats.total_attempted > 0 else 0

    # Daily puzzle activity for last 30 days
    from datetime import date, timedelta
    from sqlalchemy import func, cast, Date as SADate
    today = date.today()
    days_30 = [(today - timedelta(days=i)) for i in range(29, -1, -1)]
    raw = (PuzzleAttempt.query
        .with_entities(cast(PuzzleAttempt.attempted_at, SADate).label('day'),
                       func.count().label('cnt'))
        .filter_by(user_id=user_id)
        .filter(PuzzleAttempt.attempted_at >= today - timedelta(days=29))
        .group_by('day').all())
    activity_map = {r.day: r.cnt for r in raw}
    daily_labels  = [d.strftime('%b %d') for d in days_30]
    daily_counts  = [activity_map.get(d, 0) for d in days_30]

    return render_template('stats.html',
        active_page='stats',
        username=session.get('username'),
        user_id=user_id,
        avatar_url=avatar_url,
        member_since=user.created_at.strftime('%b %Y') if user and user.created_at else 'Unknown',
        overall_rating=user.rating if user else 1200,
        streak=stats.streak_current if stats else 0,
        puzzle_rating=stats.puzzle_rating if stats else 1200,
        total_solved=stats.total_solved if stats else 0,
        total_attempted=stats.total_attempted if stats else 0,
        accuracy=accuracy,
        recent_attempts=recent_attempts,
        daily_labels=daily_labels,
        daily_counts=daily_counts,
    )


@auth_bp.route('/api/quote', methods=['GET'])
def get_quote():
    import random
    from flask import jsonify
    quotes = [
        {"quote": "The blunders are all there on the board, waiting to be made.", "author": "Savielly Tartakower"},
        {"quote": "Chess is life.", "author": "Bobby Fischer"},
        {"quote": "Chess is the art of analysis.", "author": "Mikhail Botvinnik"},
        {"quote": "Every chess master was once a beginner.", "author": "Irving Chernev"},
        {"quote": "In life, as in chess, forethought wins.", "author": "Charles Buxton"},
        {"quote": "Chess is the gymnasium of the mind.", "author": "Blaise Pascal"},
        {"quote": "The game of chess is not merely an idle amusement.", "author": "Benjamin Franklin"},
        {"quote": "Chess holds its master in its own bonds, shackling the mind and brain so that the inner freedom of the very strongest must suffer.", "author": "Albert Einstein"},
        {"quote": "Life is like a game of chess. To win you have to make a move.", "author": "Allan Rufus"},
        {"quote": "Chess is not about winning. It's about the beauty of the moves.", "author": "Garry Kasparov"},
        {"quote": "The secret of getting ahead is getting started.", "author": "Mark Twain"},
        {"quote": "It does not matter how slowly you go as long as you do not stop.", "author": "Confucius"},
        {"quote": "Success is not final, failure is not fatal: It is the courage to continue that counts.", "author": "Winston Churchill"},
        {"quote": "The only way to do great work is to love what you do.", "author": "Steve Jobs"},
        {"quote": "In the middle of every difficulty lies opportunity.", "author": "Albert Einstein"},
        {"quote": "Imagination is more important than knowledge.", "author": "Albert Einstein"},
        {"quote": "The future belongs to those who believe in the beauty of their dreams.", "author": "Eleanor Roosevelt"},
        {"quote": "It always seems impossible until it's done.", "author": "Nelson Mandela"},
        {"quote": "Do not wait to strike till the iron is hot; but make it hot by striking.", "author": "William Butler Yeats"},
        {"quote": "Believe you can and you're halfway there.", "author": "Theodore Roosevelt"},
        {"quote": "The mind is everything. What you think you become.", "author": "Buddha"},
        {"quote": "An investment in knowledge pays the best interest.", "author": "Benjamin Franklin"},
        {"quote": "I have not failed. I've just found 10,000 ways that won't work.", "author": "Thomas Edison"},
        {"quote": "The best time to plant a tree was 20 years ago. The second best time is now.", "author": "Chinese Proverb"},
        {"quote": "You miss 100% of the shots you don't take.", "author": "Wayne Gretzky"},
        {"quote": "Whether you think you can or you think you can't, you're right.", "author": "Henry Ford"},
        {"quote": "Strive not to be a success, but rather to be of value.", "author": "Albert Einstein"},
        {"quote": "The journey of a thousand miles begins with one step.", "author": "Lao Tzu"},
        {"quote": "That which does not kill us makes us stronger.", "author": "Friedrich Nietzsche"},
        {"quote": "To be yourself in a world that is constantly trying to make you something else is the greatest accomplishment.", "author": "Ralph Waldo Emerson"},
        {"quote": "Two things are infinite: the universe and human stupidity; and I'm not sure about the universe.", "author": "Albert Einstein"},
        {"quote": "In the end, it's not the years in your life that count. It's the life in your years.", "author": "Abraham Lincoln"},
        {"quote": "The only true wisdom is in knowing you know nothing.", "author": "Socrates"},
        {"quote": "Spread love everywhere you go. Let no one ever come to you without leaving happier.", "author": "Mother Teresa"},
        {"quote": "When you reach the end of your rope, tie a knot in it and hang on.", "author": "Franklin D. Roosevelt"},
        {"quote": "Always remember that you are absolutely unique. Just like everyone else.", "author": "Margaret Mead"},
        {"quote": "Don't judge each day by the harvest you reap but by the seeds that you plant.", "author": "Robert Louis Stevenson"},
        {"quote": "The way to get started is to quit talking and begin doing.", "author": "Walt Disney"},
    ]
    return jsonify(random.choice(quotes))


@auth_bp.route('/privacy')
def privacy():
    return render_template('privacy.html')


@auth_bp.route('/tos')
def tos():
    return render_template('tos.html')

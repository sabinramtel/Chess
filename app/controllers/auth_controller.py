import re
import random
from datetime import datetime, timedelta, timezone

def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app.models.user_model import User
from app.models.email_verification_model import EmailVerification
from app.controllers.email_controller import send_otp_email
from app.controllers.base_controller import BaseController

def _generate_otp():
    return str(random.randint(100000, 999999))

class AuthController(BaseController):
    def login(self):
        """Handles user authentication (Login) via form submission or JSON API."""
        if request.method == 'POST':
            if request.is_json:
                identifier, password = self.get_json_data('identifier', 'password')
                identifier = identifier.strip() if identifier else ''
                is_api = True
            else:
                identifier, password = self.get_form_data('identifier', 'password')
                is_api = False

            if not identifier or not password:
                if is_api:
                    return jsonify({'success': False, 'message': 'All fields are required'}), 400
                flash('All fields are required.', 'error')
                return redirect(url_for('auth.login_page'))

            try:
                user_model = User()
                user_data = user_model.find_by("username", identifier)
                if not user_data:
                    user_data = user_model.find_by("email", identifier)
                
                user = User.from_db(user_data) if user_data else None
                
            except Exception as e:
                if is_api:
                    return jsonify({
                        'success': False,
                        'message': f'Database error: {str(e)}. Please check server configuration.'
                    }), 503
                flash('Database connection error. Please try again later.', 'error')
                return redirect(url_for('auth.login_page'))

            if user and user.check_password(password):
                session['user_id'] = user.id
                session['username'] = user.username
                if is_api:
                    return jsonify({'success': True, 'message': 'Welcome back! Your next move awaits.', 'username': user.username, 'redirect': '/home'}), 200
                flash('Welcome back! Your next move awaits.', 'success')
                return redirect(url_for('auth.home'))
            else:
                if is_api:
                    return jsonify({'success': False, 'message': 'Invalid username/email or password.'}), 401
                flash('Invalid username/email or password.', 'error')
                return redirect(url_for('auth.login_page'))

        return render_template('login.html')

    def check_username(self):
        username = request.args.get('username', '').strip()

        if not username or len(username) < 3:
            return jsonify({'available': False, 'message': 'At least 3 characters required'})

        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            return jsonify({'available': False, 'message': 'Letters, numbers, underscores only'})

        user_data = User().find_by("username", username)
        if user_data:
            return jsonify({'available': False, 'message': 'Username already taken'})

        return jsonify({'available': True, 'message': 'Username is available'})

    def register(self):
        data = request.get_json() or {}

        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        email            = data.get('email', '').strip()
        username         = data.get('username', '').strip()
        password         = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        agreed           = data.get('agreed', False)

        errors = {}

        if not email:
            errors['email'] = 'Email is required'
        elif not re.match(r'^[^ \s@]+@[^ \s@]+\.[^ \s@]+$', email):
            errors['email'] = 'Invalid email format'
        elif User().find_by("email", email):
            errors['email'] = 'Email already registered'

        if not username:
            errors['username'] = 'Username is required'
        elif not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            errors['username'] = '3-20 chars: letters, numbers, underscores only'
        elif User().find_by("username", username):
            errors['username'] = 'Username already taken'

        if not password:
            errors['password'] = 'Password is required'
        elif len(password) < 8:
            errors['password'] = 'Must be at least 8 characters'

        if not confirm_password:
            errors['confirm_password'] = 'Please confirm your password'
        elif password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match'

        if not agreed:
            errors['terms'] = 'You must agree to the Terms of Service'

        if errors:
            return jsonify({'success': False, 'errors': errors}), 422

        user = User(email=email, username=username)
        user.set_password(password)
        user.save()

        ev = EmailVerification(
            user_id=user.id,
            otp=None,
            is_verified=True,
            expires_at=_utcnow() + timedelta(minutes=15)
        )
        ev.save()

        session['user_id'] = user.id
        session['username'] = user.username

        return jsonify({
            'success': True,
            'message': 'Account created! Welcome to Project Chess.',
            'redirect': url_for('auth.home')
        }), 201

    def verify_email(self):
        data = request.get_json() or {}
        otp_input = data.get('otp', '').strip()

        user_id = session.get('pending_user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Session expired. Please log in again.'}), 400

        ev_data = EmailVerification().find_by("user_id", user_id)
        if not ev_data:
            return jsonify({'success': False, 'message': 'No verification record found.'}), 400
            
        ev = EmailVerification.from_db(ev_data)

        if ev.is_verified:
            user_data = User().find_by("id", user_id)
            session.pop('pending_user_id', None)
            session['user_id'] = user_data['id']
            session['username'] = user_data['username']
            return jsonify({'success': True, 'redirect': url_for('auth.home')}), 200

        if _utcnow() > ev.expires_at:
            return jsonify({'success': False, 'message': 'Code expired. Request a new one.'}), 400

        if ev.otp != otp_input:
            return jsonify({'success': False, 'message': 'Incorrect code. Try again.'}), 400

        ev.is_verified = True
        ev.otp = None
        ev.update()

        user_data = User().find_by("id", user_id)
        session.pop('pending_user_id', None)
        session['user_id'] = user_data['id']
        session['username'] = user_data['username']

        return jsonify({'success': True, 'redirect': url_for('auth.home')}), 200

    def forgot_password(self):
        data = request.get_json() or {}
        email = data.get('email', '').strip()
        if not email:
            return jsonify({'success': False, 'message': 'Email is required'}), 400

        user_data = User().find_by("email", email)
        if not user_data:
            return jsonify({'success': False, 'message': 'No account found with that email'}), 404
        user = User.from_db(user_data)

        otp = _generate_otp()
        ev_data = EmailVerification().find_by("user_id", user.id)
        if ev_data:
            ev = EmailVerification.from_db(ev_data)
            ev.otp = otp
            ev.expires_at = _utcnow() + timedelta(minutes=15)
            ev.update()
        else:
            ev = EmailVerification(
                user_id=user.id,
                otp=otp,
                is_verified=True,
                expires_at=_utcnow() + timedelta(minutes=15)
            )
            ev.save()

        send_otp_email(email, user.username, otp)

        from flask import current_app
        response = {'success': True, 'message': 'Reset code sent'}
        if current_app.debug:
            response['dev_otp'] = otp
        return jsonify(response), 200

    def reset_password(self):
        data = request.get_json() or {}
        email    = data.get('email', '').strip()
        otp      = data.get('otp', '').strip()
        new_pw   = data.get('new_password', '')

        if not email or not otp or not new_pw:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        if len(new_pw) < 8:
            return jsonify({'success': False, 'message': 'Password must be at least 8 characters'}), 400

        user_data = User().find_by("email", email)
        if not user_data:
            return jsonify({'success': False, 'message': 'Invalid request'}), 400
        user = User.from_db(user_data)

        ev_data = EmailVerification().find_by("user_id", user.id)
        if not ev_data:
            return jsonify({'success': False, 'message': 'Incorrect code'}), 400
        ev = EmailVerification.from_db(ev_data)
        
        if ev.otp != otp:
            return jsonify({'success': False, 'message': 'Incorrect code'}), 400
            
        if _utcnow() > ev.expires_at:
            return jsonify({'success': False, 'message': 'Code expired. Request a new one.'}), 400

        user.set_password(new_pw)
        user.update(user.id, update_password=True)
        
        ev.otp = None
        ev.update()
        
        return jsonify({'success': True, 'message': 'Password reset successfully'}), 200

    def resend_otp(self):
        user_id = session.get('pending_user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Session expired. Please register again.'}), 400

        ev_data = EmailVerification().find_by("user_id", user_id)
        if not ev_data:
            return jsonify({'success': False, 'message': 'Nothing to resend.'}), 400
            
        ev = EmailVerification.from_db(ev_data)
        if ev.is_verified:
            return jsonify({'success': False, 'message': 'Nothing to resend.'}), 400

        otp = _generate_otp()
        ev.otp = otp
        ev.expires_at = _utcnow() + timedelta(minutes=15)
        ev.update()

        user_data = User().find_by("id", user_id)
        send_otp_email(user_data['email'], user_data['username'], otp)

        return jsonify({'success': True, 'message': 'A new code has been sent to your email.'}), 200

    # --- Frontend Page Routes (moved from auth_routes.py) ---

    def index(self):
        if 'user_id' in session:
            return redirect(url_for('auth.home'))
        return render_template('index.html')

    def home(self):
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

    def play(self):
        from app.models.settings_model import UserSettings
        s = UserSettings.query.filter_by(user_id=session['user_id']).first()
        return render_template('play.html',
                               active_page='play',
                               username=session.get('username'),
                               user_id=session.get('user_id'),
                               board_theme=(s.board_theme if s else 'classic'))

    def puzzle_page(self):
        from app.models.settings_model import UserSettings
        s = UserSettings.query.filter_by(user_id=session['user_id']).first()
        return render_template('puzzle.html',
                               active_page='puzzle',
                               username=session.get('username'),
                               user_id=session.get('user_id'),
                               board_theme=(s.board_theme if s else 'classic'))

    def lobby(self):
        return render_template('lobby.html',
                               active_page='lobby',
                               username=session.get('username'),
                               user_id=session.get('user_id'))

    def login_page(self):
        if request.method == 'GET' and 'user_id' in session:
            return redirect(url_for('auth.home'))
        return self.login()

    def logout(self):
        session.clear()
        return redirect(url_for('auth.login_page'))

    def signup_page(self):
        if 'user_id' in session:
            return redirect(url_for('auth.home'))
        return render_template('signup.html')

    def forgot_password_page(self):
        return render_template('forgot_password.html')

    def verify_email_page(self):
        if 'pending_user_id' not in session:
            return redirect(url_for('auth.login_page'))
        return render_template('verify_otp.html')

    def user_profile(self, username):
        from app.models.user_model import User
        from app.models.puzzle_stats_model import UserPuzzleStats
        from app.models.settings_model import UserSettings
        from flask import abort
        user_data = User().find_by("username", username)
        user = User.from_db(user_data) if user_data else None
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

    def stats_page(self):
        from app.models.puzzle_stats_model import UserPuzzleStats
        from app.models.settings_model import UserSettings
        from app.models.user_model import User
        from app.models.puzzle_attempt_model import PuzzleAttempt

        user_id = session.get('user_id')
        user_data = User().find_by("id", user_id)
        user = User.from_db(user_data) if user_data else None
        stats = UserPuzzleStats.query.filter_by(user_id=user_id).first()
        user_settings = UserSettings.query.filter_by(user_id=user_id).first()
        avatar_url = user_settings.avatar_url if user_settings and user_settings.avatar_url else None

        recent_attempts = (PuzzleAttempt.query
            .filter_by(user_id=user_id)
            .order_by(PuzzleAttempt.attempted_at.desc())
            .limit(6).all())

        from app.models.game_record_model import GameRecord
        recent_games = GameRecord.find_recent_by_user_id(user_id, limit=6)

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
            recent_games=recent_games,
        )

    def get_quote(self):
        import random
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

    def privacy(self):
        return render_template('privacy.html')

    def tos(self):
        return render_template('tos.html')

    # --- Deployment-specific routes ---

    def health(self):
        return 'OK', 200

    # TEMPORARY DIAGNOSTIC HANDLER
    def handle_exception(self, e):
        # Catch everything and return the traceback
        import traceback
        tb = traceback.format_exc()
        return jsonify({
            "error": "Unhandled Exception",
            "message": str(e),
            "traceback": tb
        }), 500

    def db_status(self):
        """Diagnostic endpoint — shows DB connectivity and which env vars are set."""
        import os, re
        from flask import current_app
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


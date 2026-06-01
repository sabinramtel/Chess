from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import bcrypt
import re
import os
from dotenv import load_dotenv

load_dotenv()


# ── Database Manager ─────────────────────────────────────────────────────────

class DatabaseManager:
    """Handles all MySQL database connections."""

    def __init__(self):
        self._config = {
            'host':     os.getenv('DB_HOST', 'localhost'),
            'user':     os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'chess_signup'),
            'charset':  'utf8mb4'
        }

    def get_connection(self):
        """Create and return a new database connection."""
        return mysql.connector.connect(**self._config)

    def is_healthy(self):
        """Check if the database is reachable."""
        try:
            conn = self.get_connection()
            conn.close()
            return True, 'connected'
        except Error as e:
            return False, str(e)


# ── Validator ────────────────────────────────────────────────────────────────

class Validator:
    """Validates user input for registration and login."""

    EMAIL_RE    = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')
    USERNAME_RE = re.compile(r'^[a-zA-Z0-9_]{3,20}$')

    @classmethod
    def validate_email(cls, email):
        """Return an error message if the email is invalid, else None."""
        if not email:
            return 'Email is required'
        if not cls.EMAIL_RE.match(email):
            return 'Invalid email format'
        return None

    @classmethod
    def validate_username(cls, username):
        """Return an error message if the username is invalid, else None."""
        if not username:
            return 'Username is required'
        if not cls.USERNAME_RE.match(username):
            return '3-20 chars: letters, numbers, underscores only'
        return None

    @classmethod
    def validate_password(cls, password):
        """Return an error message if the password is invalid, else None."""
        if not password:
            return 'Password is required'
        if len(password) < 8:
            return 'Password must be at least 8 characters'
        return None

    @classmethod
    def validate_registration(cls, email, username, password, confirm_password, agreed):
        """Validate all registration fields. Returns a dict of errors (empty if valid)."""
        errors = {}

        email_err = cls.validate_email(email)
        if email_err:
            errors['email'] = email_err

        username_err = cls.validate_username(username)
        if username_err:
            errors['username'] = username_err

        password_err = cls.validate_password(password)
        if password_err:
            errors['password'] = password_err

        if not confirm_password:
            errors['confirm_password'] = 'Please confirm your password'
        elif password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match'

        if not agreed:
            errors['terms'] = 'You must agree to the Terms of Service'

        return errors

    @classmethod
    def validate_login(cls, identifier, password):
        """Validate login fields. Returns a dict of errors (empty if valid)."""
        errors = {}

        if not identifier:
            errors['identifier'] = 'Email or username is required'
        if not password:
            errors['password'] = 'Password is required'

        return errors


# ── User Service ─────────────────────────────────────────────────────────────

class UserService:
    """Handles user-related business logic: registration, login, lookups."""

    def __init__(self, db_manager):
        self._db = db_manager

    def is_username_available(self, username):
        """Check if a username is available. Returns (available: bool, message: str)."""
        conn   = self._db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
        taken = cursor.fetchone() is not None
        cursor.close()
        conn.close()

        if taken:
            return False, 'Username already taken'
        return True, 'Username available!'

    def register(self, email, username, password):
        """
        Register a new user.
        Returns (success: bool, data: dict, status_code: int).
        """
        password_hash = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')

        conn   = self._db.get_connection()
        cursor = conn.cursor()

        # Check for duplicate email
        cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
        if cursor.fetchone():
            cursor.close(); conn.close()
            return False, {'errors': {'email': 'Email already registered'}}, 409

        # Check for duplicate username
        cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            cursor.close(); conn.close()
            return False, {'errors': {'username': 'Username already taken'}}, 409

        # Insert the new user
        cursor.execute(
            'INSERT INTO users (email, username, password_hash) VALUES (%s, %s, %s)',
            (email, username, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return True, {
            'message':  'Account created successfully! Welcome to the board.',
            'user_id':  user_id,
            'username': username
        }, 201

    def authenticate(self, identifier, password):
        """
        Authenticate a user by email or username.
        Returns (success: bool, data: dict, status_code: int).
        """
        conn   = self._db.get_connection()
        cursor = conn.cursor(dictionary=True)

        # Look up by email or username
        if '@' in identifier:
            cursor.execute(
                'SELECT id, username, password_hash FROM users WHERE email = %s',
                (identifier.lower(),)
            )
        else:
            cursor.execute(
                'SELECT id, username, password_hash FROM users WHERE username = %s',
                (identifier,)
            )

        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            return False, {
                'errors': {'identifier': 'No account found with that email or username'}
            }, 401

        if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return False, {'errors': {'password': 'Incorrect password'}}, 401

        return True, {
            'message':  'Login successful!',
            'user_id':  user['id'],
            'username': user['username']
        }, 200


# ── Flask Application ────────────────────────────────────────────────────────

app = Flask(__name__)
CORS(app)

db_manager   = DatabaseManager()
user_service = UserService(db_manager)


# ── Page routes ──────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login')
def login_page():
    return render_template('login.html')


# ── API: Health check ────────────────────────────────────────────────────────

@app.route('/api/health', methods=['GET'])
def health():
    healthy, detail = db_manager.is_healthy()
    if healthy:
        return jsonify({'status': 'ok', 'database': detail})
    return jsonify({'status': 'error', 'database': detail}), 500


# ── API: Check username availability ─────────────────────────────────────────

@app.route('/api/check-username', methods=['GET'])
def check_username():
    username = request.args.get('username', '').strip()

    if not username:
        return jsonify({'available': False, 'message': 'Username required'})

    error = Validator.validate_username(username)
    if error:
        return jsonify({'available': False, 'message': error})

    try:
        available, message = user_service.is_username_available(username)
        return jsonify({'available': available, 'message': message})
    except Error:
        return jsonify({'available': False, 'message': 'Server error, try again'}), 500


# ── API: Register ────────────────────────────────────────────────────────────

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'message': 'Invalid JSON'}), 400

    email            = data.get('email', '').strip().lower()
    username         = data.get('username', '').strip()
    password         = data.get('password', '')
    confirm_password = data.get('confirm_password', '')
    agreed           = data.get('agreed', False)

    # Validate input
    errors = Validator.validate_registration(email, username, password, confirm_password, agreed)
    if errors:
        return jsonify({'success': False, 'errors': errors}), 400

    # Register user
    try:
        success, result, status = user_service.register(email, username, password)
        result['success'] = success
        return jsonify(result), status
    except Error as e:
        return jsonify({'success': False, 'message': f'Database error: {e}'}), 500


# ── API: Login ───────────────────────────────────────────────────────────────

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'message': 'Invalid JSON'}), 400

    identifier = data.get('identifier', '').strip()
    password   = data.get('password', '')

    # Validate input
    errors = Validator.validate_login(identifier, password)
    if errors:
        return jsonify({'success': False, 'errors': errors}), 400

    # Authenticate user
    try:
        success, result, status = user_service.authenticate(identifier, password)
        result['success'] = success
        return jsonify(result), status
    except Error as e:
        return jsonify({'success': False, 'message': f'Database error: {e}'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

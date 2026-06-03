import bcrypt
import re
from mysql.connector import Error
from app.models.database import DatabaseManager


class Validator:
    EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')
    USERNAME_RE = re.compile(r'^[a-zA-Z0-9_]{3,20}$')

    @classmethod
    def validate_email(cls, email):
        if not email:
            return 'Email is required'
        if not cls.EMAIL_RE.match(email):
            return 'Invalid email format'
        return None

    @classmethod
    def validate_username(cls, username):
        if not username:
            return 'Username is required'
        if not cls.USERNAME_RE.match(username):
            return '3-20 chars: letters, numbers, underscores only'
        return None

    @classmethod
    def validate_password(cls, password):
        if not password:
            return 'Password is required'
        if len(password) < 8:
            return 'Password must be at least 8 characters'
        return None

    @classmethod
    def validate_registration(cls, email, username, password, confirm_password, agreed):
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
        errors = {}
        if not identifier:
            errors['identifier'] = 'Email or username is required'
        if not password:
            errors['password'] = 'Password is required'
        return errors


class UserService:
    def __init__(self, db_manager=None):
        self._db = db_manager or DatabaseManager()

    def is_username_available(self, username):
        conn = self._db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
        taken = cursor.fetchone() is not None
        cursor.close()
        conn.close()

        if taken:
            return False, 'Username already taken'
        return True, 'Username available!'

    def register(self, email, username, password):
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        conn = self._db.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return False, {'errors': {'email': 'Email already registered'}}, 409

        cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return False, {'errors': {'username': 'Username already taken'}}, 409

        cursor.execute(
            'INSERT INTO users (email, username, password_hash) VALUES (%s, %s, %s)',
            (email, username, password_hash),
        )
        conn.commit()
        user_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return True, {
            'message': 'Account created successfully! Welcome to the board.',
            'user_id': user_id,
            'username': username,
        }, 201

    def authenticate(self, identifier, password):
        conn = self._db.get_connection()
        cursor = conn.cursor(dictionary=True)

        if '@' in identifier:
            cursor.execute('SELECT id, username, password_hash FROM users WHERE email = %s', (identifier.lower(),))
        else:
            cursor.execute('SELECT id, username, password_hash FROM users WHERE username = %s', (identifier,))

        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            return False, {'errors': {'identifier': 'No account found with that email or username'}}, 401

        if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return False, {'errors': {'password': 'Incorrect password'}}, 401

        return True, {
            'message': 'Login successful!',
            'user_id': user['id'],
            'username': user['username'],
        }, 200

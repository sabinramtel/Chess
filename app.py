from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import bcrypt
import re
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    'host':     os.getenv('DB_HOST', 'localhost'),
    'user':     os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'chess_signup'),
    'charset':  'utf8mb4'
}

EMAIL_RE    = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')
USERNAME_RE = re.compile(r'^[a-zA-Z0-9_]{3,20}$')


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


# ── Health check ──────────────────────────────────────────────────────────────

@app.route('/api/health', methods=['GET'])
def health():
    try:
        conn = get_db()
        conn.close()
        return jsonify({'status': 'ok', 'database': 'connected'})
    except Error as e:
        return jsonify({'status': 'error', 'database': str(e)}), 500


# ── Real-time username availability ──────────────────────────────────────────

@app.route('/api/check-username', methods=['GET'])
def check_username():
    username = request.args.get('username', '').strip()

    if not username:
        return jsonify({'available': False, 'message': 'Username required'})

    if not USERNAME_RE.match(username):
        return jsonify({
            'available': False,
            'message': '3-20 chars: letters, numbers, underscores only'
        })

    try:
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
        taken = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        if taken:
            return jsonify({'available': False, 'message': 'Username already taken'})
        return jsonify({'available': True, 'message': 'Username available!'})
    except Error:
        return jsonify({'available': False, 'message': 'Server error, try again'}), 500


# ── Registration ──────────────────────────────────────────────────────────────

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

    errors = {}

    if not email:
        errors['email'] = 'Email is required'
    elif not EMAIL_RE.match(email):
        errors['email'] = 'Invalid email format'

    if not username:
        errors['username'] = 'Username is required'
    elif not USERNAME_RE.match(username):
        errors['username'] = '3-20 chars: letters, numbers, underscores only'

    if not password:
        errors['password'] = 'Password is required'
    elif len(password) < 8:
        errors['password'] = 'Password must be at least 8 characters'

    if not confirm_password:
        errors['confirm_password'] = 'Please confirm your password'
    elif password != confirm_password:
        errors['confirm_password'] = 'Passwords do not match'

    if not agreed:
        errors['terms'] = 'You must agree to the Terms of Service'

    if errors:
        return jsonify({'success': False, 'errors': errors}), 400

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        conn   = get_db()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
        if cursor.fetchone():
            cursor.close(); conn.close()
            return jsonify({'success': False, 'errors': {'email': 'Email already registered'}}), 409

        cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            cursor.close(); conn.close()
            return jsonify({'success': False, 'errors': {'username': 'Username already taken'}}), 409

        cursor.execute(
            'INSERT INTO users (email, username, password_hash) VALUES (%s, %s, %s)',
            (email, username, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return jsonify({
            'success':  True,
            'message':  'Account created successfully! Welcome to the board.',
            'user_id':  user_id,
            'username': username
        }), 201

    except Error as e:
        return jsonify({'success': False, 'message': f'Database error: {e}'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

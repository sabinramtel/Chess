import re
from flask import jsonify, request
from app import db
from app.models.user import User


class AuthController:

    @staticmethod
    def check_username():
        username = request.args.get('username', '').strip()

        if not username or len(username) < 3:
            return jsonify({'available': False, 'message': 'At least 3 characters required'})

        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            return jsonify({'available': False, 'message': 'Letters, numbers, underscores only'})

        exists = User.query.filter_by(username=username).first()
        if exists:
            return jsonify({'available': False, 'message': 'Username already taken'})

        return jsonify({'available': True, 'message': 'Username is available'})

    @staticmethod
    def register():
        data = request.get_json()

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
        elif not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            errors['email'] = 'Invalid email format'
        elif User.query.filter_by(email=email).first():
            errors['email'] = 'Email already registered'

        if not username:
            errors['username'] = 'Username is required'
        elif not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            errors['username'] = '3-20 chars: letters, numbers, underscores only'
        elif User.query.filter_by(username=username).first():
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
        db.session.add(user)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'username': user.username
        }), 201

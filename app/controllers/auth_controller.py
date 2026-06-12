import re
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app import db
from app.models.user import User
 
class AuthController:
 
    @staticmethod
    def login():
        """Handles user authentication (Login) via form submission or JSON API."""
        if request.method == 'POST':
            # Support both JSON data (like your register) and standard HTML Form data
            if request.is_json:
                data = request.get_json() or {}
                identifier = data.get('identifier', '').strip()
                password = data.get('password', '')
                is_api = True
            else:
                identifier = request.form.get('identifier', '').strip()
                password = request.form.get('password', '')
                is_api = False
 
            if not identifier or not password:
                if is_api:
                    return jsonify({'success': False, 'message': 'All fields are required'}), 400
                flash('All fields are required.', 'error')
                return redirect(url_for('auth.login_page'))
 
            # Look up the user by either username or email matching your user.py layout
            user = User.query.filter((User.username == identifier) | (User.email == identifier)).first()
 
            # Check if user exists and password matches
            if user and user.check_password(password):
                session['user_id'] = user.id
                session['username'] = user.username
                if is_api:
                    return jsonify({'success': True, 'message': 'Welcome back! Your next move awaits.'}), 200
                flash('Welcome back! Your next move awaits.', 'success')
                return redirect('/')  # Redirect to your chess main menu or dashboard
            else:
                if is_api:
                    return jsonify({'success': False, 'message': 'Invalid username/email or password.'}), 401
                flash('Invalid username/email or password.', 'error')
                return redirect(url_for('auth.login_page'))
 
        # GET request renders the template
        return render_template('login.html')
 
    @staticmethod
    def check_username():
        """Asynchronously checks if a username is valid and available."""
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
        """Handles new user registration via asynchronous JSON requests."""
        data = request.get_json()
 
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
 
        email            = data.get('email', '').strip()
        username         = data.get('username', '').strip()
        password         = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        agreed           = data.get('agreed', False)
 
        errors = {}
 
        # Email Verification
        if not email:
            errors['email'] = 'Email is required'
        elif not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            errors['email'] = 'Invalid email format'
        elif User.query.filter_by(email=email).first():
            errors['email'] = 'Email already registered'
 
        # Username Verification
        if not username:
            errors['username'] = 'Username is required'
        elif not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            errors['username'] = '3-20 chars: letters, numbers, underscores only'
        elif User.query.filter_by(username=username).first():
            errors['username'] = 'Username already taken'
 
        # Password Verification
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
 
        # Create user and save to database
        user = User(email=email, username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
 
        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'username': user.username
        }), 201
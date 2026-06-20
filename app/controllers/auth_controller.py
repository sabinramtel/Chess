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

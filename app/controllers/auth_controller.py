import re
import random
from datetime import datetime, timedelta, timezone

def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app import db
from app.models.user_model import User
from app.models.email_verification_model import EmailVerification
from app.controllers.email_controller import send_otp_email


def _generate_otp():
    return str(random.randint(100000, 999999))


class AuthController:

    @staticmethod
    def login():
        """Handles user authentication (Login) via form submission or JSON API."""
        if request.method == 'POST':
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

            user = User.query.filter((User.username == identifier) | (User.email == identifier)).first()

            if user and user.check_password(password):
                # Block unverified accounts
                ev = EmailVerification.query.filter_by(user_id=user.id).first()
                if ev and not ev.is_verified:
                    session['pending_user_id'] = user.id
                    if is_api:
                        return jsonify({
                            'success': False,
                            'needs_verification': True,
                            'message': 'Please verify your email before logging in.'
                        }), 403
                    return redirect(url_for('auth.verify_email_page'))

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

        # Create user
        user = User(email=email, username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # get user.id without full commit

        # Create verification record
        otp = _generate_otp()
        ev = EmailVerification(
            user_id=user.id,
            otp=otp,
            is_verified=False,
            expires_at=_utcnow() + timedelta(minutes=15)
        )
        db.session.add(ev)
        db.session.commit()

        # Store pending user in session so verify page knows who to verify
        session['pending_user_id'] = user.id

        from flask import current_app
        send_otp_email(email, username, otp)

        response = {
            'success': True,
            'message': 'Account created! Check your email for the verification code.',
            'redirect': url_for('auth.verify_email_page')
        }
        if current_app.debug:
            response['dev_otp'] = otp

        return jsonify(response), 201

    @staticmethod
    def verify_email():
        """Validate the OTP the user submitted."""
        data = request.get_json() or {}
        otp_input = data.get('otp', '').strip()

        user_id = session.get('pending_user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Session expired. Please log in again.'}), 400

        ev = EmailVerification.query.filter_by(user_id=user_id).first()
        if not ev:
            return jsonify({'success': False, 'message': 'No verification record found.'}), 400

        if ev.is_verified:
            # Already verified — just log them in
            user = User.query.get(user_id)
            session.pop('pending_user_id', None)
            session['user_id'] = user.id
            session['username'] = user.username
            return jsonify({'success': True, 'redirect': url_for('auth.home')}), 200

        if _utcnow() > ev.expires_at:
            return jsonify({'success': False, 'message': 'Code expired. Request a new one.'}), 400

        if ev.otp != otp_input:
            return jsonify({'success': False, 'message': 'Incorrect code. Try again.'}), 400

        # Mark verified and log in
        ev.is_verified = True
        ev.otp = None
        db.session.commit()

        user = User.query.get(user_id)
        session.pop('pending_user_id', None)
        session['user_id'] = user.id
        session['username'] = user.username

        return jsonify({'success': True, 'redirect': url_for('auth.home')}), 200

    @staticmethod
    def forgot_password():
        data = request.get_json() or {}
        email = data.get('email', '').strip()
        if not email:
            return jsonify({'success': False, 'message': 'Email is required'}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'success': False, 'message': 'No account found with that email'}), 404

        otp = _generate_otp()
        ev = EmailVerification.query.filter_by(user_id=user.id).first()
        if ev:
            ev.otp = otp
            ev.expires_at = _utcnow() + timedelta(minutes=15)
        else:
            ev = EmailVerification(
                user_id=user.id,
                otp=otp,
                is_verified=True,
                expires_at=_utcnow() + timedelta(minutes=15)
            )
            db.session.add(ev)
        db.session.commit()

        send_otp_email(email, user.username, otp)

        from flask import current_app
        response = {'success': True, 'message': 'Reset code sent'}
        if current_app.debug:
            response['dev_otp'] = otp
        return jsonify(response), 200

    @staticmethod
    def reset_password():
        data = request.get_json() or {}
        email    = data.get('email', '').strip()
        otp      = data.get('otp', '').strip()
        new_pw   = data.get('new_password', '')

        if not email or not otp or not new_pw:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        if len(new_pw) < 8:
            return jsonify({'success': False, 'message': 'Password must be at least 8 characters'}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'success': False, 'message': 'Invalid request'}), 400

        ev = EmailVerification.query.filter_by(user_id=user.id).first()
        if not ev or ev.otp != otp:
            return jsonify({'success': False, 'message': 'Incorrect code'}), 400
        if _utcnow() > ev.expires_at:
            return jsonify({'success': False, 'message': 'Code expired. Request a new one.'}), 400

        user.set_password(new_pw)
        ev.otp = None
        db.session.commit()
        return jsonify({'success': True, 'message': 'Password reset successfully'}), 200

    @staticmethod
    def resend_otp():
        """Generate and resend a fresh OTP."""
        user_id = session.get('pending_user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Session expired. Please register again.'}), 400

        ev = EmailVerification.query.filter_by(user_id=user_id).first()
        if not ev or ev.is_verified:
            return jsonify({'success': False, 'message': 'Nothing to resend.'}), 400

        otp = _generate_otp()
        ev.otp = otp
        ev.expires_at = _utcnow() + timedelta(minutes=15)
        db.session.commit()

        user = User.query.get(user_id)
        send_otp_email(user.email, user.username, otp)

        return jsonify({'success': True, 'message': 'A new code has been sent to your email.'}), 200

import os
from flask import request, session, jsonify
from app import db
from app.models.user_model import User
from app.models.settings_model import UserSettings


class SettingsController:

    @staticmethod
    def get_user_and_settings():
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        s = UserSettings.query.filter_by(user_id=user_id).first()
        if not s:
            s = UserSettings(user_id=user_id)
            db.session.add(s)
            db.session.commit()
        return user, s

    @staticmethod
    def update_profile():
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401

        data = request.get_json() or {}
        user = User.query.get(user_id)
        s = UserSettings.query.filter_by(user_id=user_id).first()
        if not s:
            s = UserSettings(user_id=user_id)
            db.session.add(s)

        new_username = data.get('username', '').strip()
        if new_username and new_username != user.username:
            if User.query.filter_by(username=new_username).first():
                return jsonify({'success': False, 'message': 'Username already taken'}), 409
            user.username = new_username
            session['username'] = new_username

        s.country = data.get('country', s.country)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Profile updated'})

    @staticmethod
    def update_password():
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401

        data = request.get_json() or {}
        user = User.query.get(user_id)

        current = data.get('current_password', '')
        new_pw  = data.get('new_password', '')
        confirm = data.get('confirm_password', '')

        if not user.check_password(current):
            return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400
        if len(new_pw) < 8:
            return jsonify({'success': False, 'message': 'New password must be at least 8 characters'}), 400
        if new_pw != confirm:
            return jsonify({'success': False, 'message': 'Passwords do not match'}), 400

        user.set_password(new_pw)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Password updated'})

    @staticmethod
    def update_game():
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401

        data = request.get_json() or {}
        s = UserSettings.query.filter_by(user_id=user_id).first()
        if not s:
            s = UserSettings(user_id=user_id)
            db.session.add(s)

        s.board_theme          = data.get('board_theme', s.board_theme)
        s.piece_set            = data.get('piece_set', s.piece_set)
        s.board_orientation    = data.get('board_orientation', s.board_orientation)
        s.move_confirmation    = data.get('move_confirmation', s.move_confirmation)
        s.auto_promote_queen   = data.get('auto_promote_queen', s.auto_promote_queen)
        s.premove              = data.get('premove', s.premove)
        s.sound_effects        = data.get('sound_effects', s.sound_effects)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Game preferences updated'})

    @staticmethod
    def update_notifications():
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401

        data = request.get_json() or {}
        s = UserSettings.query.filter_by(user_id=user_id).first()
        if not s:
            s = UserSettings(user_id=user_id)
            db.session.add(s)

        s.notify_game_invites    = data.get('notify_game_invites', s.notify_game_invites)
        s.notify_friend_requests = data.get('notify_friend_requests', s.notify_friend_requests)
        s.notify_tournaments     = data.get('notify_tournaments', s.notify_tournaments)
        s.notify_your_turn       = data.get('notify_your_turn', s.notify_your_turn)
        s.notify_daily_puzzle    = data.get('notify_daily_puzzle', s.notify_daily_puzzle)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Notifications updated'})

    @staticmethod
    def update_appearance():
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401

        data = request.get_json() or {}
        s = UserSettings.query.filter_by(user_id=user_id).first()
        if not s:
            s = UserSettings(user_id=user_id)
            db.session.add(s)

        s.site_theme = data.get('site_theme', s.site_theme)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Appearance updated'})

    @staticmethod
    def update_privacy():
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401

        data = request.get_json() or {}
        s = UserSettings.query.filter_by(user_id=user_id).first()
        if not s:
            s = UserSettings(user_id=user_id)
            db.session.add(s)

        s.who_can_challenge  = data.get('who_can_challenge', s.who_can_challenge)
        s.profile_visibility = data.get('profile_visibility', s.profile_visibility)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Privacy settings updated'})

    @staticmethod
    def upload_avatar():
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401

        if 'avatar' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'}), 400

        file = request.files['avatar']
        if not file.filename:
            return jsonify({'success': False, 'message': 'No file selected'}), 400

        ext = file.filename.rsplit('.', 1)[-1].lower()
        if ext not in {'png', 'jpg', 'jpeg', 'gif', 'webp'}:
            return jsonify({'success': False, 'message': 'Invalid file type'}), 400

        upload_dir = os.path.join('app', 'static', 'avatars')
        os.makedirs(upload_dir, exist_ok=True)
        filename = f"user_{user_id}.{ext}"
        file.save(os.path.join(upload_dir, filename))

        s = UserSettings.query.filter_by(user_id=user_id).first()
        if not s:
            s = UserSettings(user_id=user_id)
            db.session.add(s)
        s.avatar_url = f'/static/avatars/{filename}'
        db.session.commit()
        return jsonify({'success': True, 'avatar_url': s.avatar_url})

    @staticmethod
    def remove_avatar():
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401

        s = UserSettings.query.filter_by(user_id=user_id).first()
        if s:
            s.avatar_url = ''
            db.session.commit()
        return jsonify({'success': True, 'message': 'Avatar removed'})

import os
from flask import request, session, jsonify, render_template
from app import db
from app.models.user_model import User
from app.models.settings_model import UserSettings


from app.controllers.base_controller import BaseController

COUNTRIES = [
    ('', 'Select country…'),
    ('AM', '🇦🇲 Armenia'), ('AR', '🇦🇷 Argentina'), ('AU', '🇦🇺 Australia'),
    ('AZ', '🇦🇿 Azerbaijan'), ('BD', '🇧🇩 Bangladesh'), ('BY', '🇧🇾 Belarus'),
    ('BR', '🇧🇷 Brazil'), ('BG', '🇧🇬 Bulgaria'), ('CA', '🇨🇦 Canada'),
    ('CN', '🇨🇳 China'), ('HR', '🇭🇷 Croatia'), ('CU', '🇨🇺 Cuba'),
    ('CZ', '🇨🇿 Czech Republic'), ('EG', '🇪🇬 Egypt'), ('FR', '🇫🇷 France'),
    ('GE', '🇬🇪 Georgia'), ('DE', '🇩🇪 Germany'), ('GR', '🇬🇷 Greece'),
    ('HU', '🇭🇺 Hungary'), ('IN', '🇮🇳 India'), ('ID', '🇮🇩 Indonesia'),
    ('IR', '🇮🇷 Iran'), ('IL', '🇮🇱 Israel'), ('IT', '🇮🇹 Italy'),
    ('JP', '🇯🇵 Japan'), ('KZ', '🇰🇿 Kazakhstan'), ('KR', '🇰🇷 South Korea'),
    ('MX', '🇲🇽 Mexico'), ('NP', '🇳🇵 Nepal'), ('NL', '🇳🇱 Netherlands'),
    ('NG', '🇳🇬 Nigeria'), ('NO', '🇳🇴 Norway'), ('PK', '🇵🇰 Pakistan'),
    ('PH', '🇵🇭 Philippines'), ('PL', '🇵🇱 Poland'), ('PT', '🇵🇹 Portugal'),
    ('RO', '🇷🇴 Romania'), ('RU', '🇷🇺 Russia'), ('RS', '🇷🇸 Serbia'),
    ('SK', '🇸🇰 Slovakia'), ('ZA', '🇿🇦 South Africa'), ('ES', '🇪🇸 Spain'),
    ('SE', '🇸🇪 Sweden'), ('TR', '🇹🇷 Turkey'), ('UA', '🇺🇦 Ukraine'),
    ('GB', '🇬🇧 United Kingdom'), ('US', '🇺🇸 United States'),
    ('UZ', '🇺🇿 Uzbekistan'), ('VN', '🇻🇳 Vietnam'),
]


class SettingsController(BaseController):

    def settings_page(self):
        user, s = self.get_user_and_settings()
        return render_template('settings.html',
                               active_page='settings',
                               username=session.get('username'),
                               user_id=session.get('user_id'),
                               user=user,
                               s=s,
                               countries=COUNTRIES)

    def get_user_and_settings(self, ):
        user_id = session.get('user_id')
        user_data = User().find_by('id', user_id)
        user = User.from_db(user_data) if user_data else None
        s = UserSettings.query.filter_by(user_id=user_id).first()
        if not s:
            s = UserSettings(user_id=user_id)
            db.session.add(s)
            db.session.commit()
        return user, s

    def update_profile(self, ):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401

        data = request.get_json() or {}
        user_data = User().find_by('id', user_id)
        user = User.from_db(user_data) if user_data else None
        s = UserSettings.query.filter_by(user_id=user_id).first()
        if not s:
            s = UserSettings(user_id=user_id)
            db.session.add(s)

        new_username = data.get('username', '').strip()
        if new_username and new_username != user.username:
            if User().find_by("username", new_username):
                return jsonify({'success': False, 'message': 'Username already taken'}), 409
            user.username = new_username
            session['username'] = new_username

        new_email = data.get('email', '').strip().lower()
        if new_email and new_email != user.email:
            if User().find_by("email", new_email):
                return jsonify({'success': False, 'message': 'Email already taken'}), 409
            user.email = new_email

        s.country = data.get('country', s.country)
        s.bio = data.get('bio', s.bio)
        user.update(user.id)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Profile updated'})

    def update_password(self, ):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401

        data = request.get_json() or {}
        user_data = User().find_by('id', user_id)
        user = User.from_db(user_data) if user_data else None

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
        user.update(user.id, update_password=True)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Password updated'})

    def update_game(self, ):
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

    def update_notifications(self, ):
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

    def update_appearance(self, ):
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

    def update_privacy(self, ):
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

    def upload_avatar(self, ):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401

        if 'avatar' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'}), 400

        file = request.files['avatar']
        if not file.filename:
            return jsonify({'success': False, 'message': 'No file selected'}), 400

        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if not ext:
            ext = 'jpg'
        allowed = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff', 'heic', 'avif'}
        if ext not in allowed:
            ext = 'jpg'  # fallback for unknown extensions

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

    def remove_avatar(self, ):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401

        s = UserSettings.query.filter_by(user_id=user_id).first()
        if s:
            s.avatar_url = ''
            db.session.commit()
        return jsonify({'success': True, 'message': 'Avatar removed'})

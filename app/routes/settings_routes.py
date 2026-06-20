from flask import Blueprint, render_template, session, redirect, url_for
from app.controllers.settings_controller import SettingsController

settings_controller = SettingsController()
 
settings_bp = Blueprint('settings', __name__)
 
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
 
 
@settings_bp.route('/settings')
def settings_page():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    user, s = settings_controller.get_user_and_settings()
    return render_template('settings.html',
                           active_page='settings',
                           username=session.get('username'),
                           user_id=session.get('user_id'),
                           user=user,
                           s=s,
                           countries=COUNTRIES)
 
 
@settings_bp.route('/api/settings/profile', methods=['POST'])
def update_profile():
    return settings_controller.update_profile()
 
 
@settings_bp.route('/api/settings/password', methods=['POST'])
def update_password():
    return settings_controller.update_password()
 
 
@settings_bp.route('/api/settings/game', methods=['POST'])
def update_game():
    return settings_controller.update_game()
 
 
@settings_bp.route('/api/settings/notifications', methods=['POST'])
def update_notifications():
    return settings_controller.update_notifications()
 
 
@settings_bp.route('/api/settings/appearance', methods=['POST'])
def update_appearance():
    return settings_controller.update_appearance()
 
 
@settings_bp.route('/api/settings/privacy', methods=['POST'])
def update_privacy():
    return settings_controller.update_privacy()
 
 
@settings_bp.route('/api/settings/avatar', methods=['POST'])
def upload_avatar():
    return settings_controller.upload_avatar()
 
 
@settings_bp.route('/api/settings/avatar', methods=['DELETE'])
def remove_avatar():
    return settings_controller.remove_avatar()
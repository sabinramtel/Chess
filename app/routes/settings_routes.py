from flask import Blueprint
from app.controllers.settings_controller import SettingsController
from app.auth import login_required


class SettingsRoutes:
    def __init__(self):
        self.bp = Blueprint('settings', __name__)
        self.controller = SettingsController()

    def register(self):
        self.bp.route('/settings')(
            login_required(self.controller.settings_page)
        )
        self.bp.route('/api/settings/profile', methods=['POST'])(
            self.controller.update_profile
        )
        self.bp.route('/api/settings/password', methods=['POST'])(
            self.controller.update_password
        )
        self.bp.route('/api/settings/game', methods=['POST'])(
            self.controller.update_game
        )
        self.bp.route('/api/settings/notifications', methods=['POST'])(
            self.controller.update_notifications
        )
        self.bp.route('/api/settings/appearance', methods=['POST'])(
            self.controller.update_appearance
        )
        self.bp.route('/api/settings/privacy', methods=['POST'])(
            self.controller.update_privacy
        )
        self.bp.route('/api/settings/avatar', methods=['POST'])(
            self.controller.upload_avatar
        )
        self.bp.route('/api/settings/avatar', methods=['DELETE'])(
            self.controller.remove_avatar
        )
        return self.bp
from flask import Blueprint
from app.controllers.game_controller import GameController


class GameRoutes:
    def __init__(self):
        self.bp = Blueprint('game', __name__, url_prefix='/api/game')
        self.controller = GameController()

    def register(self):
        self.bp.route('/create', methods=['POST'])(
            self.controller.create_game_api
        )
        self.bp.route('/move', methods=['POST'])(
            self.controller.move_api
        )
        self.bp.route('/legal-moves', methods=['POST'])(
            self.controller.legal_moves_api
        )
        self.bp.route('/state', methods=['POST'])(
            self.controller.get_state_api
        )
        self.bp.route('/resign', methods=['POST'])(
            self.controller.resign_api
        )
        self.bp.route('/draw', methods=['POST'])(
            self.controller.draw_api
        )
        self.bp.route('/save', methods=['POST'])(
            self.controller.save_api
        )

        # ── HTTP Lobby Endpoints (replaces socket lobby for Render compatibility) ──────
        self.bp.route('/create-room', methods=['POST'])(
            self.controller.create_room
        )
        self.bp.route('/join-room', methods=['POST'])(
            self.controller.join_room
        )
        self.bp.route('/room-status/<room_code>', methods=['GET'])(
            self.controller.room_status
        )

        return self.bp
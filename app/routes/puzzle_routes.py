from flask import Blueprint, request, jsonify, session as flask_session
from app import db
from app.controllers.puzzle_controller import PuzzleController
from app.controllers.puzzle_logic import PuzzleLogic


class PuzzleRoutes:
    def __init__(self):
        self.bp = Blueprint('puzzle', __name__, url_prefix='/api/puzzle')

    def _ctrl(self) -> PuzzleController:
        """Factory that wires up the controller per request."""
        return PuzzleController(db.session)

    def _user_id(self, data: dict | None = None) -> int | None:
        """Resolve user_id from JSON body, query string, or session."""
        if data:
            uid = data.get('user_id')
            if uid:
                return int(uid)
        uid = request.args.get('user_id', type=int)
        if uid:
            return uid
        return flask_session.get('user_id')

    # ── GET /api/puzzle/next?user_id= ─────────────────────────────────────────────

    def _get_next_puzzle(self):
        user_id = self._user_id()
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400

        puzzle, stats = self._ctrl().get_next_puzzle(user_id)
        if not puzzle:
            return jsonify({'error': 'No puzzles available'}), 404

        # Compute the FEN after the opponent's setup move
        logic = PuzzleLogic(puzzle.fen, puzzle.moves)
        fen_after_setup = logic.board_after_setup().fen()

        return jsonify({
            'puzzle':          puzzle.to_dict(),
            'fen_after_setup': fen_after_setup,
            'user_rating':     stats.puzzle_rating,
        })

    # ── POST /api/puzzle/attempt ──────────────────────────────────────────────────

    def _submit_attempt(self):
        data       = request.get_json() or {}
        user_id    = self._user_id(data)
        puzzle_id  = data.get('puzzle_id')
        move       = (data.get('move') or '').strip()
        move_index = int(data.get('move_index', 0))

        if not all([user_id, puzzle_id, move]):
            return jsonify({'error': 'user_id, puzzle_id, and move are required'}), 400

        result = self._ctrl().check_move(user_id, int(puzzle_id), move, move_index)

        if 'error' in result:
            return jsonify(result), 404

        return jsonify(result)

    # ── GET /api/puzzle/stats?user_id= ───────────────────────────────────────────

    def _get_stats(self):
        user_id = self._user_id()
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400

        return jsonify(self._ctrl().get_stats(user_id))

    def register(self):
        self.bp.route('/next', methods=['GET'])(self._get_next_puzzle)
        self.bp.route('/attempt', methods=['POST'])(self._submit_attempt)
        self.bp.route('/stats', methods=['GET'])(self._get_stats)
        return self.bp

from flask import Blueprint, request, jsonify, session as flask_session

from app import db
from app.repositories.puzzle_repository import PuzzleRepository
from app.services.puzzle_service import PuzzleService
from app.services.puzzle_logic import PuzzleLogic

puzzle_bp = Blueprint('puzzle', __name__, url_prefix='/api/puzzle')


def _svc() -> PuzzleService:
    """Factory that wires up the dependency chain per request."""
    repo = PuzzleRepository(db.session)
    return PuzzleService(repo, db.session)


def _user_id(data: dict | None = None) -> int | None:
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

@puzzle_bp.route('/next', methods=['GET'])
def get_next_puzzle():
    """
    Return a puzzle near the caller's current puzzle rating.

    Response
    --------
    {
      puzzle: { id, puzzle_id, fen, setup_move, rating, themes },
      fen_after_setup: "<FEN string after setup move>",
      user_rating: 1200
    }
    The client should display fen_after_setup so the user sees the position
    they must solve from.  setup_move is provided for animation purposes.
    """
    user_id = _user_id()
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    puzzle, stats = _svc().get_next_puzzle(user_id)
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

@puzzle_bp.route('/attempt', methods=['POST'])
def submit_attempt():
    """
    Validate one user move inside a puzzle.

    Request body (JSON)
    -------------------
    {
      "user_id":    1,
      "puzzle_id":  42,
      "move":       "e2e4",   ← UCI format
      "move_index": 0         ← 0 = first user move, 1 = second, …
    }

    Response
    --------
    {
      "correct":        true,
      "opponent_reply": "d7d5",   ← null when puzzle is complete
      "complete":       false,
      "expected":       null       ← filled in when correct=false (hint)
    }
    """
    data       = request.get_json() or {}
    user_id    = _user_id(data)
    puzzle_id  = data.get('puzzle_id')
    move       = (data.get('move') or '').strip()
    move_index = int(data.get('move_index', 0))

    if not all([user_id, puzzle_id, move]):
        return jsonify({'error': 'user_id, puzzle_id, and move are required'}), 400

    result = _svc().check_move(user_id, int(puzzle_id), move, move_index)

    if 'error' in result:
        return jsonify(result), 404

    return jsonify(result)


# ── GET /api/puzzle/stats?user_id= ───────────────────────────────────────────

@puzzle_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    Return the user's puzzle statistics.

    Response
    --------
    {
      "puzzle_rating":   1250,
      "streak_current":  3,
      "total_solved":    18,
      "total_attempted": 25
    }
    """
    user_id = _user_id()
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    return jsonify(_svc().get_stats(user_id))

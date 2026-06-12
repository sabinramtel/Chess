from flask import Blueprint, request, jsonify, session
from app.controllers.game import GameController
from app.models.piece import Color
from functools import wraps
import uuid

game_bp = Blueprint('game', __name__, url_prefix='/api/game')

# In-memory game storage
active_games = {}

def require_game(f):
    """Decorator to require a valid game session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        game_id = request.json.get('game_id') if request.json else None
        if not game_id or game_id not in active_games:
            return jsonify({'error': 'Game not found'}), 404
        kwargs['game'] = active_games[game_id]
        return f(*args, **kwargs)
    return decorated_function

@game_bp.route('/create', methods=['POST'])
def create_game():
    """Create a new game."""
    data = request.json or {}
    white_username = data.get('white_username', 'White')
    black_username = data.get('black_username', 'Black')
    time_control = data.get('time_control', 600)
    increment = data.get('increment', 0)
    
    game = GameController.create_game(white_username, black_username, time_control, increment)
    game_id = str(uuid.uuid4())
    active_games[game_id] = game
    
    return jsonify({
        'game_id': game_id,
        'game_state': game.to_dict()
    }), 201

@game_bp.route('/move', methods=['POST'])
@require_game
def move(game):
    """Make a move in the game."""
    data = request.json or {}
    from_sq = tuple(data.get('from_sq', []))
    to_sq = tuple(data.get('to_sq', []))
    promotion = data.get('promotion')
    
    result = GameController.make_move(game, from_sq, to_sq, promotion)
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code

@game_bp.route('/legal-moves', methods=['POST'])
@require_game
def legal_moves(game):
    """Get legal moves from a square."""
    data = request.json or {}
    square = tuple(data.get('square', []))
    
    moves = GameController.get_legal_moves(game, square)
    return jsonify({
        'square': square,
        'legal_moves': moves
    }), 200

@game_bp.route('/state', methods=['POST'])
@require_game
def get_state(game):
    """Get current game state."""
    return jsonify(game.to_dict()), 200

@game_bp.route('/resign', methods=['POST'])
@require_game
def resign(game):
    """Resign from the game."""
    data = request.json or {}
    color = data.get('color', 'white')
    color_enum = Color.WHITE if color == 'white' else Color.BLACK
    
    result = GameController.resign(game, color_enum)
    return jsonify(result), 200

@game_bp.route('/draw', methods=['POST'])
@require_game
def draw(game):
    """Offer/accept draw."""
    result = GameController.offer_draw(game)
    return jsonify(result), 200

@game_bp.route('/save', methods=['POST'])
@require_game
def save(game):
    """Save completed game."""
    data = request.json or {}
    white_user_id = data.get('white_user_id')
    black_user_id = data.get('black_user_id')
    
    record = GameController.save_game_record(game, white_user_id, black_user_id)
    return jsonify(record.to_dict()), 201
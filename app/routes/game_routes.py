from flask import Blueprint, request, jsonify, session
from app.controllers.game_controller import GameController
from app.models.piece_model import Color
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


# ── HTTP Lobby Endpoints (replaces socket lobby for Render compatibility) ──────

@game_bp.route('/create-room', methods=['POST'])
def create_room():
    """Create a multiplayer room and return the room code."""
    try:
        from app.controllers.socket_controller import active_rooms, _make_room_code
        import random
        data = request.json or {}
        username = (data.get('username') or session.get('username') or 'Player').strip()
        # Validate and convert time control and increment safely
        try:
            time_control = int(data.get('time_control', 180))
        except (ValueError, TypeError):
            time_control = 180
        try:
            increment = int(data.get('increment', 0))
        except (ValueError, TypeError):
            increment = 0
        room_code = _make_room_code()
        color = random.choice(['white', 'black'])
        active_rooms[room_code] = {
            'creator': {'sid': None, 'username': username, 'color': color},
            'white': {'username': username} if color == 'white' else None,
            'black': {'username': username} if color == 'black' else None,
            'game': None,
            'time_control': time_control,
            'increment': increment,
            'draw_offered_by': None,
            'status': 'waiting',
        }
        return jsonify({'room_code': room_code, 'color': color}), 201
    except Exception as e:
        import traceback, sys
        sys.stderr.write(f"[create_room error] {e}\n{traceback.format_exc()}\n")
        return jsonify({'error': 'Failed to create room', 'details': str(e)}), 500


@game_bp.route('/join-room', methods=['POST'])
def join_room_http():
    """Join an existing room. Starts the game immediately."""
    try:
        from app.controllers.socket_controller import active_rooms
        from app.controllers.game_controller import GameController
        data = request.json or {}
        username = (data.get('username') or session.get('username') or 'Player').strip()
        room_code = (data.get('room_code') or '').strip().upper()
        if not room_code:
            return jsonify({'success': False, 'message': 'Room code required'}), 400
        if room_code not in active_rooms:
            return jsonify({'success': False, 'message': 'Room not found'}), 404
        room = active_rooms[room_code]
        if room.get('status') != 'waiting':
            return jsonify({'success': False, 'message': 'Game already started'}), 409
        creator = room['creator']
        creator_color = creator.get('color', 'white')
        joiner_color = 'black' if creator_color == 'white' else 'white'
        if joiner_color == 'white':
            room['white'] = {'username': username}
        else:
            room['black'] = {'username': username}
        white_username = room['white']['username'] if room['white'] else username
        black_username = room['black']['username'] if room['black'] else username
        game = GameController.create_game(
            white_username,
            black_username,
            room['time_control'],
            room['increment']
        )
        room['game'] = game
        room['status'] = 'started'
        return jsonify({
            'success': True,
            'room_code': room_code,
            'color': joiner_color,
            'white_username': white_username,
            'black_username': black_username,
            'game_state': game.to_dict(),
        }), 200
    except Exception as e:
        import traceback, sys
        sys.stderr.write(f"[join_room_http error] {e}\n{traceback.format_exc()}\n")
        return jsonify({'error': 'Failed to join room', 'details': str(e)}), 500


@game_bp.route('/room-status/<room_code>', methods=['GET'])
def room_status(room_code):
    """Poll this endpoint to detect when the opponent has joined."""
    from app.controllers.socket_controller import active_rooms

    room = active_rooms.get(room_code.upper())
    if not room:
        return jsonify({'status': 'not_found'}), 404

    if room.get('status') == 'started' and room.get('game'):
        game = room['game']
        return jsonify({
            'status': 'started',
            'white_username': room['white']['username'] if room['white'] else '',
            'black_username': room['black']['username'] if room['black'] else '',
            'game_state': game.to_dict(),
        }), 200

    return jsonify({'status': 'waiting'}), 200
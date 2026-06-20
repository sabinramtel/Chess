from flask import request, jsonify, session
from app.models.game_model import Game
from app.models.player_model import Player
from app.models.piece_model import Color
from app.controllers.base_controller import BaseController
from functools import wraps
import uuid


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


class GameController(BaseController):
    """Controller for chess game operations."""

    def create_game(self, white_username, black_username, time_control=600, increment=0):
        """Create and return a new Game instance."""
        white_player = Player(white_username, Color.WHITE, time_control, increment)
        black_player = Player(black_username, Color.BLACK, time_control, increment)
        game = Game(white_player, black_player)
        # Start the white player's timer immediately
        white_player.timer.start()
        return game

    def make_move(self, game, from_sq, to_sq, promotion=None):
        """Attempt a move and return a result dict."""
        # Map promotion string to piece class if provided
        promotion_piece = None
        if promotion:
            from app.models.piece_model import Queen, Rook, Bishop, Knight
            piece_map = {
                'queen': Queen,
                'rook': Rook,
                'bishop': Bishop,
                'knight': Knight,
            }
            promotion_piece = piece_map.get(promotion.lower())

        move = game.make_move(from_sq, to_sq, promotion_piece)

        if move is None:
            return {
                'success': False,
                'error': 'Illegal move',
                'game_state': game.to_dict(),
            }

        return {
            'success': True,
            'move': move.to_dict(),
            'game_state': game.to_dict(),
        }

    def get_legal_moves(self, game, square):
        """Return a list of legal destination squares from the given square."""
        return game.get_legal_moves(square)

    def resign(self, game, color):
        """Resign for the given color."""
        game.resign(color)
        return {
            'success': True,
            'game_state': game.to_dict(),
        }

    def offer_draw(self, game):
        """Accept a draw offer (both sides agreed)."""
        game.offer_draw()
        return {
            'success': True,
            'game_state': game.to_dict(),
        }

    def save_game_record(self, game, white_user_id=None, black_user_id=None):
        """
        Persist a completed game record.

        Returns the game state dict because we are using MySQL (no ORM model).
        In a full implementation this would INSERT a row into a games table.
        """
        record = game.to_dict()
        record['white_user_id'] = white_user_id
        record['black_user_id'] = black_user_id

        # Wrap in a lightweight object so the route can call .to_dict() on it
        class _Record:
            def __init__(self, data):
                self._data = data

            def to_dict(self):
                return self._data

        return _Record(record)

    # ── HTTP API methods (called from routes) ──────────────────────────────

    def create_game_api(self):
        """Create a new game."""
        data = request.json or {}
        white_username = data.get('white_username', 'White')
        black_username = data.get('black_username', 'Black')
        time_control = data.get('time_control', 600)
        increment = data.get('increment', 0)

        game = self.create_game(white_username, black_username, time_control, increment)
        game_id = str(uuid.uuid4())
        active_games[game_id] = game

        return jsonify({
            'game_id': game_id,
            'game_state': game.to_dict()
        }), 201

    @require_game
    def move_api(self, game):
        """Make a move in the game."""
        data = request.json or {}
        from_sq = tuple(data.get('from_sq', []))
        to_sq = tuple(data.get('to_sq', []))
        promotion = data.get('promotion')

        result = self.make_move(game, from_sq, to_sq, promotion)
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code

    @require_game
    def legal_moves_api(self, game):
        """Get legal moves from a square."""
        data = request.json or {}
        square = tuple(data.get('square', []))

        moves = self.get_legal_moves(game, square)
        return jsonify({
            'square': square,
            'legal_moves': moves
        }), 200

    @require_game
    def get_state_api(self, game):
        """Get current game state."""
        return jsonify(game.to_dict()), 200

    @require_game
    def resign_api(self, game):
        """Resign from the game."""
        data = request.json or {}
        color = data.get('color', 'white')
        color_enum = Color.WHITE if color == 'white' else Color.BLACK

        result = self.resign(game, color_enum)
        return jsonify(result), 200

    @require_game
    def draw_api(self, game):
        """Offer/accept draw."""
        result = self.offer_draw(game)
        return jsonify(result), 200

    @require_game
    def save_api(self, game):
        """Save completed game."""
        data = request.json or {}
        white_user_id = data.get('white_user_id')
        black_user_id = data.get('black_user_id')

        record = self.save_game_record(game, white_user_id, black_user_id)
        return jsonify(record.to_dict()), 201

    # ── HTTP Lobby Endpoints (replaces socket lobby for Render compatibility) ──────

    def create_room(self):
        """Create a multiplayer room and return the room code."""
        try:
            from app.controllers.socket_controller import active_rooms, _make_room_code
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
            # Creator gets white, guest gets black when the second player joins.
            # Store the creator without a color slot for now.
            active_rooms[room_code] = {
                'creator': {'sid': None, 'username': username, 'color': None},
                'white': None,
                'black': None,
                'game': None,
                'time_control': time_control,
                'increment': increment,
                'draw_offered_by': None,
                'status': 'waiting',
            }
            # Return 'pending' so the lobby knows the color isn't set yet
            return jsonify({'room_code': room_code, 'color': 'pending'}), 201
        except Exception as e:
            import traceback, sys
            sys.stderr.write(f"[create_room error] {e}\n{traceback.format_exc()}\n")
            return jsonify({'error': 'Failed to create room', 'details': str(e)}), 500

    def join_room(self):
        """Join an existing room. Creator gets white, guest gets black, and starts the game."""
        try:
            import random
            from app.controllers.socket_controller import active_rooms

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
            creator_username = creator['username']
            if username.lower() == creator_username.lower():
                return jsonify({'success': False, 'message': 'You cannot join your own room'}), 403
            # Creator always gets white (first move), joiner gets black
            creator_color = 'white'
            joiner_color  = 'black'
            creator['color'] = creator_color
            room['white'] = {'username': creator_username if creator_color == 'white' else username}
            room['black'] = {'username': creator_username if creator_color == 'black' else username}
            white_username = room['white']['username']
            black_username = room['black']['username']
            game = self.create_game(
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
                'creator_color': creator_color,
                'white_username': white_username,
                'black_username': black_username,
                'game_state': game.to_dict(),
            }), 200
        except Exception as e:
            import traceback, sys
            sys.stderr.write(f"[join_room_http error] {e}\n{traceback.format_exc()}\n")
            return jsonify({'error': 'Failed to join room', 'details': str(e)}), 500

    def room_status(self, room_code):
        """Poll this endpoint to detect when the opponent has joined."""
        from app.controllers.socket_controller import active_rooms

        room = active_rooms.get(room_code.upper())
        if not room:
            return jsonify({'status': 'not_found'}), 404

        if room.get('status') == 'started' and room.get('game'):
            game = room['game']
            creator_color = room['creator'].get('color', 'white')
            return jsonify({
                'status': 'started',
                'color': creator_color,          # tell the creator their final color
                'white_username': room['white']['username'] if room['white'] else '',
                'black_username': room['black']['username'] if room['black'] else '',
                'game_state': game.to_dict(),
            }), 200

        return jsonify({'status': 'waiting'}), 200

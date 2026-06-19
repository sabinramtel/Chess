"""
app/sockets.py
--------------
All Socket.IO event handlers for real-time multiplayer chess.

Room lifecycle
--------------
  create_game  →  room created, creator waits
  join_room    →  second player joins → game starts automatically
  move         →  validated server-side, broadcast to both players
  chat         →  broadcast to room
  draw_offer   →  broadcast to room; other player responds with draw_accept/draw_decline
  resign       →  broadcast game_over to room
  disconnect   →  notify opponent
"""

import random
import string
from flask_socketio import emit, join_room, leave_room
from flask import request
from app import socketio
from app.controllers.game_controller import GameController
from app.models.piece_model import Color

# ── In-memory room store ──────────────────────────────────────────────────────
# Structure: { room_code: RoomData }
active_rooms: dict[str, dict] = {}

# Map socket-id → room_code so we can handle disconnects
sid_to_room: dict[str, str] = {}


def _make_room_code(length: int = 6) -> str:
    """Generate a short unique room code (e.g. 'A3KX92')."""
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choices(chars, k=length))
        if code not in active_rooms:
            return code


# ── Helper ────────────────────────────────────────────────────────────────────

def _room_game_state(room: dict) -> dict | None:
    """Return the serialised game state, or None if game not started."""
    game = room.get('game')
    return game.to_dict() if game else None


# ══════════════════════════════════════════════════════════════════════════════
#  CREATE GAME
# ══════════════════════════════════════════════════════════════════════════════
@socketio.on('create_game')
def handle_create_game(data):
    """
    Client sends:
        { username, time_control (optional, seconds), increment (optional) }
    Server responds to creator only:
        room_created  { room_code, color:'pending' }
    """
    username = (data.get('username') or 'Player').strip() or 'Player'
    time_control = int(data.get('time_control', 600))
    increment = int(data.get('increment', 0))

    room_code = _make_room_code()

    active_rooms[room_code] = {
        'creator': {'sid': request.sid, 'username': username},
        'white': None,
        'black': None,
        'game': None,
        'time_control': time_control,
        'increment': increment,
        'draw_offered_by': None,
    }
    sid_to_room[request.sid] = room_code

    join_room(room_code)
    emit('room_created', {'room_code': room_code, 'color': 'pending'})


# ══════════════════════════════════════════════════════════════════════════════
#  JOIN GAME
# ══════════════════════════════════════════════════════════════════════════════
@socketio.on('join_game')
def handle_join_game(data):
    """
    Client sends:
        { username, room_code }
    If the room exists and only has one player → start the game.
    Emits to the joiner:
        joined_game  { room_code, color: randomized, game_state }
    Emits to the creator:
        game_started { game_state, white_username, black_username, color: randomized }
    """
    room_code = (data.get('room_code') or '').strip().upper()
    username = (data.get('username') or 'Player').strip() or 'Player'

    # ── Validation ────────────────────────────────────────────────────────────
    if room_code not in active_rooms:
        emit('error', {'message': f'Room "{room_code}" not found.'})
        return

    room = active_rooms[room_code]

    if room['white'] is not None or room['black'] is not None:
        emit('error', {'message': 'Room is already full.'})
        return

    if room['creator']['sid'] == request.sid:
        emit('error', {'message': 'You cannot join your own room.'})
        return

    # ── Register second player & Randomize Colors ─────────────────────────────
    creator_data = room['creator']
    guest_data = {'sid': request.sid, 'username': username}
    sid_to_room[request.sid] = room_code
    join_room(room_code)

    if random.choice([True, False]):
        room['white'] = creator_data
        room['black'] = guest_data
        creator_color = 'white'
        guest_color = 'black'
    else:
        room['white'] = guest_data
        room['black'] = creator_data
        creator_color = 'black'
        guest_color = 'white'

    # ── Create the game ───────────────────────────────────────────────────────
    game = GameController.create_game(
        white_username=room['white']['username'],
        black_username=room['black']['username'],
        time_control=room['time_control'],
        increment=room['increment'],
    )
    room['game'] = game
    state = game.to_dict()

    # Tell the joiner their colour
    emit('joined_game', {
        'room_code': room_code,
        'color': guest_color,
        'game_state': state,
        'white_username': room['white']['username'],
        'black_username': room['black']['username'],
    })

    # Tell the creator their colour and start the game
    emit('game_started', {
        'game_state': state,
        'white_username': room['white']['username'],
        'black_username': room['black']['username'],
        'color': creator_color,
    }, to=creator_data['sid'])


# ══════════════════════════════════════════════════════════════════════════════
#  MOVE
# ══════════════════════════════════════════════════════════════════════════════
@socketio.on('move')
def handle_move(data):
    """
    Client sends:
        { room_code, from_sq:[r,c], to_sq:[r,c], promotion (optional) }
    Broadcasts to room on success:
        move_made  { move, game_state }
    Emits error to sender on failure:
        move_error { message }
    """
    room_code = (data.get('room_code') or '').upper()
    if room_code not in active_rooms:
        emit('move_error', {'message': 'Room not found'})
        return

    room = active_rooms[room_code]
    game = room.get('game')
    if not game:
        emit('move_error', {'message': 'Game not started yet'})
        return

    # Enforce turn: only the player whose turn it is may move
    current_turn = game.current_turn  # Color enum
    expected_sid = room['white']['sid'] if current_turn == Color.WHITE else room['black']['sid']
    if request.sid != expected_sid:
        emit('move_error', {'message': "It's not your turn"})
        return

    from_sq = tuple(data.get('from_sq', []))
    to_sq = tuple(data.get('to_sq', []))
    promotion = data.get('promotion')

    result = GameController.make_move(game, from_sq, to_sq, promotion)

    if not result['success']:
        emit('move_error', {'message': result.get('error', 'Illegal move')})
        return

    emit('move_made', {
        'move': result['move'],
        'game_state': result['game_state'],
    }, to=room_code)

    # Broadcast game over when checkmate or stalemate is detected
    status = result['game_state'].get('status')
    if status == 'checkmate':
        emit('game_over', {
            'reason': 'checkmate',
            'winner': result['game_state'].get('winner'),
            'game_state': result['game_state'],
        }, to=room_code)
    elif status == 'stalemate':
        emit('game_over', {
            'reason': 'draw',
            'winner': None,
            'game_state': result['game_state'],
        }, to=room_code)


# ══════════════════════════════════════════════════════════════════════════════
#  CHAT
# ══════════════════════════════════════════════════════════════════════════════
@socketio.on('chat')
def handle_chat(data):
    """
    Client sends:
        { room_code, message, username }
    Broadcasts to room:
        chat_message  { username, message }
    """
    room_code = (data.get('room_code') or '').upper()
    message = (data.get('message') or '').strip()
    username = (data.get('username') or 'Player').strip()

    if not message or room_code not in active_rooms:
        return

    emit('chat_message', {
        'username': username,
        'message': message,
    }, to=room_code)


# ══════════════════════════════════════════════════════════════════════════════
#  RESIGN
# ══════════════════════════════════════════════════════════════════════════════
@socketio.on('resign')
def handle_resign(data):
    """
    Client sends:
        { room_code, color:'white'|'black' }
    Broadcasts to room:
        game_over  { reason:'resigned', winner, game_state }
    """
    room_code = (data.get('room_code') or '').upper()
    color_str = data.get('color', 'white')

    if room_code not in active_rooms:
        return

    room = active_rooms[room_code]
    game = room.get('game')
    if not game:
        return

    color = Color.WHITE if color_str == 'white' else Color.BLACK
    GameController.resign(game, color)
    winner = 'black' if color_str == 'white' else 'white'

    emit('game_over', {
        'reason': 'resigned',
        'winner': winner,
        'game_state': game.to_dict(),
    }, to=room_code)


# ══════════════════════════════════════════════════════════════════════════════
#  DRAW OFFER / ACCEPT / DECLINE
# ══════════════════════════════════════════════════════════════════════════════
@socketio.on('draw_offer')
def handle_draw_offer(data):
    """
    Client sends:  { room_code, color }
    Broadcasts:    draw_offered  { offered_by }
    """
    room_code = (data.get('room_code') or '').upper()
    color = data.get('color', 'white')

    if room_code not in active_rooms:
        return

    active_rooms[room_code]['draw_offered_by'] = color
    emit('draw_offered', {'offered_by': color}, to=room_code)


@socketio.on('draw_accept')
def handle_draw_accept(data):
    """
    Client sends:  { room_code }
    Broadcasts:    game_over  { reason:'draw', game_state }
    """
    room_code = (data.get('room_code') or '').upper()
    if room_code not in active_rooms:
        return

    room = active_rooms[room_code]
    game = room.get('game')
    if not game:
        return

    GameController.offer_draw(game)
    emit('game_over', {
        'reason': 'draw',
        'winner': None,
        'game_state': game.to_dict(),
    }, to=room_code)


@socketio.on('draw_decline')
def handle_draw_decline(data):
    """
    Client sends:  { room_code }
    Broadcasts:    draw_declined  {}
    """
    room_code = (data.get('room_code') or '').upper()
    if room_code not in active_rooms:
        return

    active_rooms[room_code]['draw_offered_by'] = None
    emit('draw_declined', {}, to=room_code)


# ══════════════════════════════════════════════════════════════════════════════
<<<<<<< HEAD
#  REJOIN ROOM  (called by play.html on reconnect after lobby → play navigation)
=======
#  LEGAL MOVES REQUEST  (highlights for the clicking player)
# ══════════════════════════════════════════════════════════════════════════════
@socketio.on('request_legal_moves')
def handle_request_legal_moves(data):
    """
    Client sends:
        { room_code, square:[r,c] }
    Responds to sender only:
        legal_moves_response  { legal_moves: [[r,c], ...] }
    """
    room_code = (data.get('room_code') or '').upper()
    square = tuple(data.get('square', []))

    if room_code not in active_rooms:
        emit('legal_moves_response', {'legal_moves': []})
        return

    room = active_rooms[room_code]
    game = room.get('game')
    if not game:
        emit('legal_moves_response', {'legal_moves': []})
        return

    # Only allow the player whose turn it is to request moves
    expected_sid = (
        room['white']['sid'] if game.current_turn == Color.WHITE else room['black']['sid']
    )
    if request.sid != expected_sid:
        emit('legal_moves_response', {'legal_moves': []})
        return

    legal_moves = game.get_legal_moves(square)
    emit('legal_moves_response', {'legal_moves': legal_moves})


# ══════════════════════════════════════════════════════════════════════════════
#  REJOIN  (reconnect to an existing room after a page reload)
>>>>>>> origin/main
# ══════════════════════════════════════════════════════════════════════════════
@socketio.on('rejoin_room')
def handle_rejoin_room(data):
    """
    Client sends:
        { room_code, color, username }
<<<<<<< HEAD
    Re-registers the socket SID in the room so moves keep working after the
    browser navigates from lobby.html to play.html (which resets the WS connection).
    """
    room_code = (data.get('room_code') or '').strip().upper()
    color = data.get('color', '').strip()
    username = (data.get('username') or 'Player').strip()

    if room_code not in active_rooms:
        emit('error', {'message': f'Room "{room_code}" not found.'})
=======
    Responds to sender with the current game state so the board re-renders.
    """
    room_code = (data.get('room_code') or '').upper()
    color = data.get('color', 'white')
    username = data.get('username', 'Player')

    if room_code not in active_rooms:
>>>>>>> origin/main
        return

    room = active_rooms[room_code]
    join_room(room_code)
    sid_to_room[request.sid] = room_code

<<<<<<< HEAD
    # Update the SID for this player's color slot
=======
    # Update the stored sid so future events route correctly
>>>>>>> origin/main
    if color == 'white' and room.get('white'):
        room['white']['sid'] = request.sid
    elif color == 'black' and room.get('black'):
        room['black']['sid'] = request.sid
<<<<<<< HEAD
    else:
        # Game not started yet (creator navigated directly to play)
        # Update creator SID
        if room['creator']['username'] == username:
            room['creator']['sid'] = request.sid

    game = room.get('game')
    if game:
        emit('game_started', {
            'game_state': game.to_dict(),
            'white_username': room['white']['username'] if room.get('white') else '',
            'black_username': room['black']['username'] if room.get('black') else '',
=======

    game = room.get('game')
    if game:
        white_name = room['white']['username'] if room.get('white') else username
        black_name = room['black']['username'] if room.get('black') else username
        emit('game_started', {
            'game_state': game.to_dict(),
            'white_username': white_name,
            'black_username': black_name,
>>>>>>> origin/main
            'color': color,
        })


# ══════════════════════════════════════════════════════════════════════════════
<<<<<<< HEAD
#  LEGAL MOVES  (for move-highlight UI in play.html)
# ══════════════════════════════════════════════════════════════════════════════
@socketio.on('request_legal_moves')
def handle_request_legal_moves(data):
    """
    Client sends:
        { room_code, square: [row, col] }
    Server responds to requester only:
        legal_moves_response  { legal_moves: [[r,c], ...] }
    """
    room_code = (data.get('room_code') or '').upper()
    square = data.get('square')

    if room_code not in active_rooms:
        emit('legal_moves_response', {'legal_moves': []})
        return

    room = active_rooms[room_code]
    game = room.get('game')
    if not game or not square:
        emit('legal_moves_response', {'legal_moves': []})
        return

    legal = GameController.get_legal_moves(game, tuple(square))
    emit('legal_moves_response', {'legal_moves': legal})


# ══════════════════════════════════════════════════════════════════════════════
#  DISCONNECT
# ══════════════════════════════════════════════════════════════════════════════
@socketio.on('disconnect')
def handle_disconnect():
    """Notify the opponent when a player disconnects mid-game."""
    sid = request.sid
    room_code = sid_to_room.pop(sid, None)
    if not room_code or room_code not in active_rooms:
        return

    room = active_rooms[room_code]
    game = room.get('game')

    # Determine who left
    if room.get('white') and room['white']['sid'] == sid:
        who = 'white'
        winner = 'black'
    elif room.get('black') and room['black']['sid'] == sid:
        who = 'black'
        winner = 'white'
    else:
        return

    # Only broadcast abandonment if the game was in progress
    if game and game.status.value == 'ongoing':
        emit('player_disconnected', {
            'color': who,
            'winner': winner,
            'message': f'{who.capitalize()} player disconnected. {winner.capitalize()} wins!',
        }, to=room_code)

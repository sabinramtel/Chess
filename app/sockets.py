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
from app.controllers.game import GameController
from app.models.piece import Color

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
        'black_username': username,
    }, to=room_code)


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
    if room['white'] and room['white']['sid'] == sid:
        who = 'white'
        winner = 'black'
    elif room['black'] and room['black']['sid'] == sid:
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

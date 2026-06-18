from app.models.game_model import Game
from app.models.player_model import Player
from app.models.piece_model import Color


class GameController:
    """Controller for chess game operations."""

    @staticmethod
    def create_game(white_username, black_username, time_control=600, increment=0):
        """Create and return a new Game instance."""
        white_player = Player(white_username, Color.WHITE, time_control, increment)
        black_player = Player(black_username, Color.BLACK, time_control, increment)
        game = Game(white_player, black_player)
        # Start the white player's timer immediately
        white_player.timer.start()
        return game

    @staticmethod
    def make_move(game, from_sq, to_sq, promotion=None):
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

    @staticmethod
    def get_legal_moves(game, square):
        """Return a list of legal destination squares from the given square."""
        return game.get_legal_moves(square)

    @staticmethod
    def resign(game, color):
        """Resign for the given color."""
        game.resign(color)
        return {
            'success': True,
            'game_state': game.to_dict(),
        }

    @staticmethod
    def offer_draw(game):
        """Accept a draw offer (both sides agreed)."""
        game.offer_draw()
        return {
            'success': True,
            'game_state': game.to_dict(),
        }

    @staticmethod
    def save_game_record(game, white_user_id=None, black_user_id=None):
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

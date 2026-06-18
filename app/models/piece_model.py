from abc import ABC, abstractmethod
from enum import Enum

class Color(Enum):
    WHITE = "white"
    BLACK = "black"

class Piece(ABC):
    """Abstract base class for all chess pieces."""

    def __init__(self, color, position=None):
        self.color = color
        self.position = position
        self.has_moved = False

    @abstractmethod
    def get_legal_moves(self, board):
        pass

    @abstractmethod
    def get_symbol(self):
        pass

    def __repr__(self):
        return self.get_symbol()


class Pawn(Piece):
    def get_symbol(self):
        return '♙' if self.color == Color.WHITE else '♟'

    def get_legal_moves(self, board):
        moves = []
        if not self.position:
            return moves

        row, col = self.position
        direction = -1 if self.color == Color.WHITE else 1
        start_row = 6 if self.color == Color.WHITE else 1

        next_row = row + direction
        if 0 <= next_row < 8:
            # Forward move
            if board.get_piece((next_row, col)) is None:
                moves.append((next_row, col))
                # Double push from starting square
                if row == start_row:
                    double_row = row + 2 * direction
                    if board.get_piece((double_row, col)) is None:
                        moves.append((double_row, col))

            # Diagonal captures
            for dc in [-1, 1]:
                next_col = col + dc
                if 0 <= next_col < 8:
                    target = board.get_piece((next_row, next_col))
                    if target and target.color != self.color:
                        moves.append((next_row, next_col))

            # En passant
            if board.en_passant_square:
                ep_row, ep_col = board.en_passant_square
                if ep_row == next_row and abs(ep_col - col) == 1:
                    moves.append((ep_row, ep_col))

        return moves


class Knight(Piece):
    def get_symbol(self):
        return '♘' if self.color == Color.WHITE else '♞'

    def get_legal_moves(self, board):
        moves = []
        if not self.position:
            return moves

        row, col = self.position
        deltas = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]

        for dr, dc in deltas:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                target = board.get_piece((new_row, new_col))
                if target is None or target.color != self.color:
                    moves.append((new_row, new_col))

        return moves


class Bishop(Piece):
    def get_symbol(self):
        return '♗' if self.color == Color.WHITE else '♝'

    def get_legal_moves(self, board):
        return self._get_sliding_moves(board, [(-1, -1), (-1, 1), (1, -1), (1, 1)])


class Rook(Piece):
    def get_symbol(self):
        return '♖' if self.color == Color.WHITE else '♜'

    def get_legal_moves(self, board):
        return self._get_sliding_moves(board, [(-1, 0), (1, 0), (0, -1), (0, 1)])


class Queen(Piece):
    def get_symbol(self):
        return '♕' if self.color == Color.WHITE else '♛'

    def get_legal_moves(self, board):
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
        return self._get_sliding_moves(board, directions)


class King(Piece):
    def get_symbol(self):
        return '♔' if self.color == Color.WHITE else '♚'

    def get_legal_moves(self, board):
        moves = []
        if not self.position:
            return moves

        row, col = self.position

        # Normal one-square moves
        for dr, dc in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                target = board.get_piece((new_row, new_col))
                if target is None or target.color != self.color:
                    moves.append((new_row, new_col))

        # Castling — structural checks only; attack checks happen in Game._get_legal_moves_for
        if not self.has_moved:
            rights = board.castling_rights.get(self.color, {})

            # Kingside: squares f,g must be empty; rook on h must not have moved
            if rights.get('kingside'):
                rook = board.get_piece((row, 7))
                if (rook is not None and not rook.has_moved
                        and board.get_piece((row, 5)) is None
                        and board.get_piece((row, 6)) is None):
                    moves.append((row, 6))

            # Queenside: squares b,c,d must be empty; rook on a must not have moved
            if rights.get('queenside'):
                rook = board.get_piece((row, 0))
                if (rook is not None and not rook.has_moved
                        and board.get_piece((row, 1)) is None
                        and board.get_piece((row, 2)) is None
                        and board.get_piece((row, 3)) is None):
                    moves.append((row, 2))

        return moves

    def _get_sliding_moves(self, board, directions):
        """Shared helper for Bishop, Rook, Queen."""
        moves = []
        if not self.position:
            return moves

        row, col = self.position

        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            while 0 <= new_row < 8 and 0 <= new_col < 8:
                target = board.get_piece((new_row, new_col))
                if target is None:
                    moves.append((new_row, new_col))
                elif target.color != self.color:
                    moves.append((new_row, new_col))
                    break
                else:
                    break
                new_row += dr
                new_col += dc

        return moves


# Share the sliding helper across sliding piece classes
for cls in [Bishop, Rook, Queen]:
    cls._get_sliding_moves = King._get_sliding_moves

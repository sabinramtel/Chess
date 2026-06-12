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
            target = board.get_piece((next_row, col))
            if target is None:
                moves.append((next_row, col))
                
                if row == start_row:
                    double_row = row + 2 * direction
                    if board.get_piece((double_row, col)) is None:
                        moves.append((double_row, col))
        
        for dc in [-1, 1]:
            next_col = col + dc
            if 0 <= next_row < 8 and 0 <= next_col < 8:
                target = board.get_piece((next_row, next_col))
                if target and target.color != self.color:
                    moves.append((next_row, next_col))
        
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
            (0, -1), (0, 1),
            (1, -1), (1, 0), (1, 1)
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
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1), (0, 1),
            (1, -1), (1, 0), (1, 1)
        ]
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                target = board.get_piece((new_row, new_col))
                if target is None or target.color != self.color:
                    moves.append((new_row, new_col))
        
        return moves
    
    def _get_sliding_moves(self, board, directions):
        """Helper for sliding pieces."""
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


# Add _get_sliding_moves to sliding pieces
for cls in [Bishop, Rook, Queen]:
    cls._get_sliding_moves = King._get_sliding_moves
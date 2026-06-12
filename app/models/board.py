from .piece import Pawn, Rook, Knight, Bishop, Queen, King, Color

class Board:
    """8x8 chess board with pieces."""
    
    def __init__(self):
        self.grid = [[None for _ in range(8)] for _ in range(8)]
        self.en_passant_square = None
        self.castling_rights = {
            Color.WHITE: {'kingside': True, 'queenside': True},
            Color.BLACK: {'kingside': True, 'queenside': True}
        }
    
    def setup_initial_position(self):
        """Set up the standard chess starting position."""
        # White pieces
        self.grid[7][0] = Rook(Color.WHITE, (7, 0))
        self.grid[7][1] = Knight(Color.WHITE, (7, 1))
        self.grid[7][2] = Bishop(Color.WHITE, (7, 2))
        self.grid[7][3] = Queen(Color.WHITE, (7, 3))
        self.grid[7][4] = King(Color.WHITE, (7, 4))
        self.grid[7][5] = Bishop(Color.WHITE, (7, 5))
        self.grid[7][6] = Knight(Color.WHITE, (7, 6))
        self.grid[7][7] = Rook(Color.WHITE, (7, 7))
        
        for col in range(8):
            self.grid[6][col] = Pawn(Color.WHITE, (6, col))
        
        # Black pieces
        for col in range(8):
            self.grid[1][col] = Pawn(Color.BLACK, (1, col))
        
        self.grid[0][0] = Rook(Color.BLACK, (0, 0))
        self.grid[0][1] = Knight(Color.BLACK, (0, 1))
        self.grid[0][2] = Bishop(Color.BLACK, (0, 2))
        self.grid[0][3] = Queen(Color.BLACK, (0, 3))
        self.grid[0][4] = King(Color.BLACK, (0, 4))
        self.grid[0][5] = Bishop(Color.BLACK, (0, 5))
        self.grid[0][6] = Knight(Color.BLACK, (0, 6))
        self.grid[0][7] = Rook(Color.BLACK, (0, 7))
    
    def get_piece(self, square):
        if not isinstance(square, tuple) or len(square) != 2:
            return None
        row, col = square
        if not (0 <= row < 8 and 0 <= col < 8):
            return None
        return self.grid[row][col]
    
    def set_piece(self, square, piece):
        row, col = square
        if 0 <= row < 8 and 0 <= col < 8:
            self.grid[row][col] = piece
            if piece:
                piece.position = square
    
    def move_piece(self, from_sq, to_sq, promotion_piece=None):
        piece = self.get_piece(from_sq)
        if not piece:
            return None
        
        captured = self.get_piece(to_sq)
        
        if promotion_piece and isinstance(piece, Pawn):
            new_piece = promotion_piece(piece.color, to_sq)
            new_piece.has_moved = True
            self.set_piece(to_sq, new_piece)
            self.set_piece(from_sq, None)
        else:
            piece.has_moved = True
            self.set_piece(to_sq, piece)
            self.set_piece(from_sq, None)
        
        return captured
    
    def is_square_attacked(self, square, by_color):
        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]
                if piece and piece.color == by_color:
                    legal_moves = piece.get_legal_moves(self)
                    if square in legal_moves:
                        return True
        return False
    
    def find_king(self, color):
        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]
                if isinstance(piece, King) and piece.color == color:
                    return (row, col)
        return None
    
    def to_dict(self):
        return {
            'grid': [
                [piece.get_symbol() if piece else None for piece in row]
                for row in self.grid
            ],
            'en_passant_square': self.en_passant_square,
            'castling_rights': self.castling_rights
        }
    
    def to_fen(self):
        fen_parts = []
        for row in self.grid:
            empty = 0
            for piece in row:
                if piece:
                    if empty:
                        fen_parts.append(str(empty))
                        empty = 0
                    fen_parts.append(piece.get_symbol())
                else:
                    empty += 1
            if empty:
                fen_parts.append(str(empty))
            fen_parts.append('/')
        return ''.join(fen_parts[:-1])
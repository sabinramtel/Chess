class Move:
    """Represents a single chess move."""
    
    def __init__(self, from_sq, to_sq, piece, captured_piece=None, 
                 notation=None, is_check=False, is_checkmate=False):
        self.from_sq = from_sq
        self.to_sq = to_sq
        self.piece = piece
        self.captured_piece = captured_piece
        self.notation = notation
        self.is_check = is_check
        self.is_checkmate = is_checkmate
        self.special_flags = set()
        self.timestamp = None
    
    def add_special_flag(self, flag):
        self.special_flags.add(flag)
    
    def to_dict(self):
        return {
            'from_sq': self.from_sq,
            'to_sq': self.to_sq,
            'piece': str(self.piece),
            'captured': str(self.captured_piece) if self.captured_piece else None,
            'notation': self.notation,
            'is_check': self.is_check,
            'is_checkmate': self.is_checkmate,
            'special_flags': list(self.special_flags)
        }


class MoveHistory:
    """Manages the history of moves in a game."""
    
    def __init__(self):
        self.moves = []
    
    def append(self, move):
        self.moves.append(move)
    
    def get_last_move(self):
        return self.moves[-1] if self.moves else None
    
    def get_moves(self):
        return self.moves
    
    def get_move_count(self):
        return len(self.moves)
    
    def get_pgn(self):
        pgn_moves = []
        for i, move in enumerate(self.moves):
            move_num = (i // 2) + 1
            if i % 2 == 0:
                pgn_moves.append(f"{move_num}. {move.notation}")
            else:
                pgn_moves.append(move.notation)
        return ' '.join(pgn_moves)
    
    def to_dict(self):
        return {
            'total_moves': len(self.moves),
            'moves': [move.to_dict() for move in self.moves]
        }
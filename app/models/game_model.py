from enum import Enum
from .board_model import Board
from .player_model import Player
from .move_model import Move, MoveHistory
from .piece_model import Color, King, Pawn
from datetime import datetime

class GameStatus(Enum):
    ONGOING = "ongoing"
    CHECK = "check"
    CHECKMATE = "checkmate"
    STALEMATE = "stalemate"
    DRAW = "draw"
    RESIGNED = "resigned"
    TIMEOUT = "timeout"

class Game:
    """Orchestrates a chess game."""
    
    def __init__(self, white_player, black_player):
        self.white_player = white_player
        self.black_player = black_player
        self.board = Board()
        self.board.setup_initial_position()
        
        self.current_turn = Color.WHITE
        self.move_history = MoveHistory()
        self.status = GameStatus.ONGOING
        self.winner = None
        self.created_at = datetime.now()
        self.ended_at = None
    
    def get_current_player(self):
        return self.white_player if self.current_turn == Color.WHITE else self.black_player
    
    def get_opponent_player(self):
        return self.black_player if self.current_turn == Color.WHITE else self.white_player
    
    def make_move(self, from_sq, to_sq, promotion_piece=None):
        piece = self.board.get_piece(from_sq)
        
        if not piece or piece.color != self.current_turn:
            return None
        
        legal_moves = self.get_legal_moves(from_sq)
        if to_sq not in legal_moves:
            return None
        
        captured = self.board.move_piece(from_sq, to_sq, promotion_piece)
        
        notation = self._generate_notation(from_sq, to_sq, piece, captured)
        move = Move(from_sq, to_sq, piece, captured, notation)
        
        if isinstance(piece, King) and abs(from_sq[1] - to_sq[1]) == 2:
            move.add_special_flag('castling')
        if isinstance(piece, Pawn) and captured is None and from_sq[1] != to_sq[1]:
            move.add_special_flag('en_passant')
        if promotion_piece:
            move.add_special_flag('promotion')
        
        self.move_history.append(move)
        opponent_color = Color.BLACK if self.current_turn == Color.WHITE else Color.WHITE
        
        if self.is_in_check(opponent_color):
            move.is_check = True
            if self.is_checkmate(opponent_color):
                move.is_checkmate = True
                self.status = GameStatus.CHECKMATE
                self.winner = self.current_turn
                self.ended_at = datetime.now()
        elif self.is_stalemate(opponent_color):
            self.status = GameStatus.STALEMATE
            self.ended_at = datetime.now()
        
        self.get_current_player().timer.pause()
        self.current_turn = opponent_color
        self.get_current_player().timer.start()
        
        return move
    
    def get_legal_moves(self, square):
        piece = self.board.get_piece(square)
        if not piece or piece.color != self.current_turn:
            return []
        
        legal = []
        for move_sq in piece.get_legal_moves(self.board):
            original_piece = self.board.get_piece(move_sq)
            self.board.set_piece(move_sq, piece)
            self.board.set_piece(square, None)
            
            king_sq = self.board.find_king(self.current_turn)
            opponent_color = Color.BLACK if self.current_turn == Color.WHITE else Color.WHITE
            if king_sq and not self.board.is_square_attacked(king_sq, opponent_color):
                legal.append(move_sq)
            
            self.board.set_piece(square, piece)
            self.board.set_piece(move_sq, original_piece)
        
        return legal
    
    def is_in_check(self, color):
        king_sq = self.board.find_king(color)
        if not king_sq:
            return False
        opponent_color = Color.BLACK if color == Color.WHITE else Color.WHITE
        return self.board.is_square_attacked(king_sq, opponent_color)
    
    def is_checkmate(self, color):
        if not self.is_in_check(color):
            return False
        
        for row in range(8):
            for col in range(8):
                piece = self.board.get_piece((row, col))
                if piece and piece.color == color:
                    if self.get_legal_moves((row, col)):
                        return False
        return True
    
    def is_stalemate(self, color):
        if self.is_in_check(color):
            return False
        
        for row in range(8):
            for col in range(8):
                piece = self.board.get_piece((row, col))
                if piece and piece.color == color:
                    if self.get_legal_moves((row, col)):
                        return False
        return True
    
    def resign(self, color):
        self.status = GameStatus.RESIGNED
        self.winner = Color.BLACK if color == Color.WHITE else Color.WHITE
        self.ended_at = datetime.now()
        if self.get_current_player().color == color:
            self.get_current_player().timer.pause()
    
    def offer_draw(self):
        self.status = GameStatus.DRAW
        self.ended_at = datetime.now()
    
    def _generate_notation(self, from_sq, to_sq, piece, captured):
        if isinstance(piece, Pawn):
            notation = ''
            if captured:
                notation += chr(ord('a') + from_sq[1]) + 'x'
            notation += chr(ord('a') + to_sq[1]) + str(8 - to_sq[0])
            return notation
        else:
            piece_char = piece.get_symbol()
            target = chr(ord('a') + to_sq[1]) + str(8 - to_sq[0])
            if captured:
                return piece_char + 'x' + target
            return piece_char + target
    
    def to_dict(self):
        return {
            'white_player': self.white_player.to_dict(),
            'black_player': self.black_player.to_dict(),
            'board': self.board.to_dict(),
            'current_turn': self.current_turn.value,
            'status': self.status.value,
            'winner': self.winner.value if self.winner else None,
            'move_count': self.move_history.get_move_count(),
            'last_move': self.move_history.get_last_move().to_dict() if self.move_history.get_last_move() else None
        }
from .time import Timer

class Player:
    """Represents a player in a chess game."""
    
    def __init__(self, username, color, initial_time=600, increment=0):
        self.username = username
        self.color = color
        self.timer = Timer(initial_time, increment)
        self.captured_pieces = []
    
    def add_captured_piece(self, piece):
        self.captured_pieces.append(piece)
    
    def get_captured_material(self):
        return self.captured_pieces
    
    def get_material_value(self):
        values = {'♙': 1, '♟': 1, '♖': 5, '♜': 5, 
                  '♗': 3, '♝': 3, '♘': 3, '♞': 3, 
                  '♕': 9, '♛': 9}
        return sum(values.get(str(p), 0) for p in self.captured_pieces)
    
    def to_dict(self):
        return {
            'username': self.username,
            'color': self.color.value,
            'timer': self.timer.to_dict(),
            'captured_pieces': [str(p) for p in self.captured_pieces],
            'material_value': self.get_material_value()
        }
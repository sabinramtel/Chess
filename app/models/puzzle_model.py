from app import db


class Puzzle(db.Model):
    __tablename__ = 'puzzles'

    id        = db.Column(db.Integer, primary_key=True, autoincrement=True)
    puzzle_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    fen       = db.Column(db.Text, nullable=False)
    moves     = db.Column(db.Text, nullable=False)   # space-separated UCI; moves[0] = opponent setup
    rating    = db.Column(db.Integer, nullable=False, index=True)
    themes    = db.Column(db.String(500), nullable=True)

    def setup_move(self) -> str:
        return self.moves.split()[0]

    def solution_moves(self) -> list[str]:
        """moves[1:] — alternates user/opponent starting with the user."""
        return self.moves.split()[1:]

    def to_dict(self) -> dict:
        parts = self.moves.split()
        return {
            'id':         self.id,
            'puzzle_id':  self.puzzle_id,
            'fen':        self.fen,
            'setup_move': parts[0] if parts else None,
            'rating':     self.rating,
            'themes':     self.themes.split() if self.themes else [],
        }

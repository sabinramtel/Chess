from datetime import datetime
from app import db


class PuzzleAttempt(db.Model):
    __tablename__ = 'puzzle_attempts'

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    puzzle_id    = db.Column(db.Integer, db.ForeignKey('puzzles.id'), nullable=False, index=True)
    solved       = db.Column(db.Boolean, default=False, nullable=False)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


    puzzle = db.relationship('Puzzle', backref='attempts')

from datetime import datetime
from app import db


class UserPuzzleStats(db.Model):
    __tablename__ = 'user_puzzle_stats'

    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    puzzle_rating    = db.Column(db.Integer, default=1200, nullable=False)
    streak_current   = db.Column(db.Integer, default=0, nullable=False)
    streak_last_date = db.Column(db.Date, nullable=True)
    total_solved     = db.Column(db.Integer, default=0, nullable=False)
    total_attempted  = db.Column(db.Integer, default=0, nullable=False)

    user = db.relationship('User', backref=db.backref('puzzle_stats', uselist=False))

    def to_dict(self) -> dict:
        return {
            'puzzle_rating':   self.puzzle_rating,
            'streak_current':  self.streak_current,
            'total_solved':    self.total_solved,
            'total_attempted': self.total_attempted,
        }

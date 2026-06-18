from datetime import date, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.puzzle_model import Puzzle
from app.models.puzzle_stats_model import UserPuzzleStats
from app.models.puzzle_attempt_model import PuzzleAttempt
from app.controllers.puzzle_logic import PuzzleLogic

_ELO_K = 32
_MIN_RATING = 100

class PuzzleController:
    def __init__(self, session: Session):
        self.session = session

    # Repository logic
    def find_by_id(self, puzzle_id: int) -> Puzzle | None:
        return self.session.get(Puzzle, puzzle_id)

    def find_near_rating(self, rating: int, exclude_ids: list[int] | None = None, window: int = 200) -> Puzzle | None:
        query = self.session.query(Puzzle).filter(
            Puzzle.rating.between(rating - window, rating + window)
        )
        if exclude_ids:
            query = query.filter(~Puzzle.id.in_(exclude_ids))
        return query.order_by(func.rand()).first()

    def get_or_create_stats(self, user_id: int) -> UserPuzzleStats:
        stats = self.session.query(UserPuzzleStats).filter_by(user_id=user_id).first()
        if not stats:
            stats = UserPuzzleStats(user_id=user_id)
            self.session.add(stats)
            self.session.flush()
        return stats

    def get_recent_attempt_puzzle_ids(self, user_id: int, limit: int = 20) -> list[int]:
        rows = (
            self.session.query(PuzzleAttempt.puzzle_id)
            .filter_by(user_id=user_id)
            .order_by(PuzzleAttempt.attempted_at.desc())
            .limit(limit)
            .all()
        )
        return [r.puzzle_id for r in rows]

    def save_attempt(self, attempt: PuzzleAttempt) -> None:
        self.session.add(attempt)

    # Service logic
    def get_next_puzzle(self, user_id: int) -> tuple[Puzzle | None, UserPuzzleStats]:
        stats = self.get_or_create_stats(user_id)
        exclude_ids = self.get_recent_attempt_puzzle_ids(user_id)
        puzzle = self.find_near_rating(stats.puzzle_rating, exclude_ids, window=200)
        if puzzle is None:
            puzzle = self.find_near_rating(stats.puzzle_rating, window=500)
        self.session.commit()
        return puzzle, stats

    def check_move(self, user_id: int, puzzle_id: int, move_uci: str, move_index: int) -> dict:
        puzzle = self.find_by_id(puzzle_id)
        if not puzzle:
            return {'error': 'Puzzle not found'}
        logic = PuzzleLogic(puzzle.fen, puzzle.moves)
        correct = logic.validate_user_move(move_uci, move_index)
        opponent_reply = None
        complete = False
        if correct:
            complete = logic.is_complete(move_index)
            if not complete:
                opponent_reply = logic.get_opponent_reply(move_index)
        if complete or not correct:
            solved = correct and complete
            self._record_attempt(user_id, puzzle_id, solved, puzzle)
        return {
            'correct': correct,
            'opponent_reply': opponent_reply,
            'complete': complete,
            'expected': logic.expected_move(move_index) if not correct else None,
        }

    def get_stats(self, user_id: int) -> dict:
        stats = self.get_or_create_stats(user_id)
        self.session.commit()
        return stats.to_dict()

    def _record_attempt(self, user_id: int, puzzle_id: int, solved: bool, puzzle: Puzzle) -> None:
        stats = self.get_or_create_stats(user_id)
        attempt = PuzzleAttempt(user_id=user_id, puzzle_id=puzzle_id, solved=solved)
        self.save_attempt(attempt)
        stats.total_attempted += 1
        self._apply_elo(stats, puzzle.rating, won=solved)
        if solved:
            stats.total_solved += 1
            self._update_streak(stats)
        self.session.commit()

    def _apply_elo(self, stats: UserPuzzleStats, puzzle_rating: int, won: bool) -> None:
        expected = 1.0 / (1.0 + 10 ** ((puzzle_rating - stats.puzzle_rating) / 400.0))
        actual = 1.0 if won else 0.0
        stats.puzzle_rating = max(_MIN_RATING, int(stats.puzzle_rating + _ELO_K * (actual - expected)))

    def _update_streak(self, stats: UserPuzzleStats) -> None:
        today = date.today()
        if stats.streak_last_date == today:
            return
        if stats.streak_last_date == today - timedelta(days=1):
            stats.streak_current += 1
        else:
            stats.streak_current = 1
        stats.streak_last_date = today

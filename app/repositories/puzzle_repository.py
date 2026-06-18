from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.puzzle import Puzzle
from app.models.puzzle_stats import UserPuzzleStats
from app.models.puzzle_attempt import PuzzleAttempt


class PuzzleRepository:
    """All database access for the puzzle feature. Receives the SQLAlchemy session
    via constructor so it can be swapped or mocked in tests."""

    def __init__(self, session: Session):
        self.session = session

    # ── Puzzles ───────────────────────────────────────────────────────────────

    def find_by_id(self, puzzle_id: int) -> Puzzle | None:
        return self.session.get(Puzzle, puzzle_id)

    def find_near_rating(
        self,
        rating: int,
        exclude_ids: list[int] | None = None,
        window: int = 200,
    ) -> Puzzle | None:
        query = self.session.query(Puzzle).filter(
            Puzzle.rating.between(rating - window, rating + window)
        )
        if exclude_ids:
            query = query.filter(~Puzzle.id.in_(exclude_ids))
        return query.order_by(func.rand()).first()

    # ── User stats ────────────────────────────────────────────────────────────

    def get_or_create_stats(self, user_id: int) -> UserPuzzleStats:
        stats = (
            self.session.query(UserPuzzleStats)
            .filter_by(user_id=user_id)
            .first()
        )
        if not stats:
            stats = UserPuzzleStats(user_id=user_id)
            self.session.add(stats)
            self.session.flush()
        return stats

    # ── Attempts ──────────────────────────────────────────────────────────────

    def get_recent_attempt_puzzle_ids(
        self, user_id: int, limit: int = 20
    ) -> list[int]:
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

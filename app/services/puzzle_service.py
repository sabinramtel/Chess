from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.puzzle import Puzzle
from app.models.puzzle_stats import UserPuzzleStats
from app.models.puzzle_attempt import PuzzleAttempt
from app.repositories.puzzle_repository import PuzzleRepository
from app.services.puzzle_logic import PuzzleLogic

_ELO_K = 32
_MIN_RATING = 100


class PuzzleService:
    """
    Business logic for the puzzle feature.

    Dependencies are injected so callers control the DB session lifetime
    and the repository implementation can be swapped in tests.
    """

    def __init__(self, repo: PuzzleRepository, session: Session):
        self.repo    = repo
        self.session = session

    # ── Public API ────────────────────────────────────────────────────────────

    def get_next_puzzle(self, user_id: int) -> tuple[Puzzle | None, UserPuzzleStats]:
        """Pick the next unseen puzzle near the user's current puzzle rating."""
        stats       = self.repo.get_or_create_stats(user_id)
        exclude_ids = self.repo.get_recent_attempt_puzzle_ids(user_id)

        puzzle = self.repo.find_near_rating(stats.puzzle_rating, exclude_ids, window=200)
        if puzzle is None:
            # Widen search window when no match in ±200
            puzzle = self.repo.find_near_rating(stats.puzzle_rating, window=500)

        self.session.commit()
        return puzzle, stats

    def check_move(
        self,
        user_id:    int,
        puzzle_id:  int,
        move_uci:   str,
        move_index: int,
    ) -> dict:
        """
        Validate a single user move.

        Returns a dict with:
          correct         – bool
          opponent_reply  – UCI str or None
          complete        – bool (True when puzzle is fully solved)
          expected        – correct UCI shown only on failure (for hint UI)
        """
        puzzle = self.repo.find_by_id(puzzle_id)
        if not puzzle:
            return {'error': 'Puzzle not found'}

        logic   = PuzzleLogic(puzzle.fen, puzzle.moves)
        correct = logic.validate_user_move(move_uci, move_index)

        opponent_reply = None
        complete       = False

        if correct:
            complete = logic.is_complete(move_index)
            if not complete:
                opponent_reply = logic.get_opponent_reply(move_index)

        # Finalise the attempt when the puzzle ends (solved or first wrong move)
        if complete or not correct:
            solved = correct and complete
            self._record_attempt(user_id, puzzle_id, solved, puzzle)

        return {
            'correct':        correct,
            'opponent_reply': opponent_reply,
            'complete':       complete,
            'expected':       logic.expected_move(move_index) if not correct else None,
        }

    def get_stats(self, user_id: int) -> dict:
        stats = self.repo.get_or_create_stats(user_id)
        self.session.commit()
        return stats.to_dict()

    # ── Private helpers ───────────────────────────────────────────────────────

    def _record_attempt(
        self,
        user_id:   int,
        puzzle_id: int,
        solved:    bool,
        puzzle:    Puzzle,
    ) -> None:
        stats = self.repo.get_or_create_stats(user_id)

        attempt = PuzzleAttempt(
            user_id=user_id,
            puzzle_id=puzzle_id,
            solved=solved,
        )
        self.repo.save_attempt(attempt)

        stats.total_attempted += 1
        self._apply_elo(stats, puzzle.rating, won=solved)

        if solved:
            stats.total_solved += 1
            self._update_streak(stats)

        self.session.commit()

    def _apply_elo(self, stats: UserPuzzleStats, puzzle_rating: int, won: bool) -> None:
        expected = 1.0 / (1.0 + 10 ** ((puzzle_rating - stats.puzzle_rating) / 400.0))
        actual   = 1.0 if won else 0.0
        stats.puzzle_rating = max(
            _MIN_RATING,
            int(stats.puzzle_rating + _ELO_K * (actual - expected)),
        )

    def _update_streak(self, stats: UserPuzzleStats) -> None:
        today = date.today()
        if stats.streak_last_date == today:
            return  # Already counted a solve today
        if stats.streak_last_date == today - timedelta(days=1):
            stats.streak_current += 1
        else:
            stats.streak_current = 1
        stats.streak_last_date = today

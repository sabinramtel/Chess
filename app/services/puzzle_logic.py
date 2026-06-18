"""
Pure chess logic for puzzle validation — no Flask, no database, no side-effects.

Lichess puzzle move format
--------------------------
  moves[0]  → opponent's setup move (auto-played before user sees board)
  moves[1]  → user's first move          (move_index = 0)
  moves[2]  → opponent's first reply
  moves[3]  → user's second move         (move_index = 1)
  moves[4]  → opponent's second reply
  ...

In solution_moves (= moves[1:]):
  user move at move_index i  →  solution_moves[i * 2]
  opponent reply after i     →  solution_moves[i * 2 + 1]
"""

import chess


class PuzzleLogic:

    def __init__(self, fen: str, moves_str: str):
        all_moves      = moves_str.split()
        self.fen       = fen
        self.setup_move     = all_moves[0]
        self.solution_moves = all_moves[1:]   # [user0, opp0, user1, opp1, ...]

    # ── Board helpers ─────────────────────────────────────────────────────────

    def board_after_setup(self) -> chess.Board:
        """Board state after the opponent's setup move — what the user sees."""
        board = chess.Board(self.fen)
        board.push_uci(self.setup_move)
        return board

    def _board_before_user_move(self, move_index: int) -> chess.Board:
        """Board right before the user's (move_index)-th move."""
        board = self.board_after_setup()
        for i in range(move_index):
            board.push_uci(self.solution_moves[i * 2])      # user move i
            board.push_uci(self.solution_moves[i * 2 + 1])  # opponent reply
        return board

    # ── Validation ────────────────────────────────────────────────────────────

    def validate_user_move(self, move_uci: str, move_index: int) -> bool:
        """
        Return True if move_uci is correct at move_index.
        A move is accepted if it matches the scripted UCI exactly, OR if it
        delivers checkmate (any checkmate wins).
        """
        solution_idx = move_index * 2
        if solution_idx >= len(self.solution_moves):
            return False

        if move_uci == self.solution_moves[solution_idx]:
            return True

        # Accept any legal checkmate as an alternative win
        board = self._board_before_user_move(move_index)
        try:
            move = chess.Move.from_uci(move_uci)
            if move in board.legal_moves:
                board.push(move)
                return board.is_checkmate()
        except ValueError:
            pass

        return False

    # ── Game-flow helpers ─────────────────────────────────────────────────────

    def get_opponent_reply(self, move_index: int) -> str | None:
        """UCI of the opponent's reply after move_index, or None if puzzle ends."""
        reply_idx = move_index * 2 + 1
        return self.solution_moves[reply_idx] if reply_idx < len(self.solution_moves) else None

    def is_complete(self, move_index: int) -> bool:
        """True when the user has played their last move in the line."""
        next_user_idx = (move_index + 1) * 2
        return next_user_idx >= len(self.solution_moves)

    def expected_move(self, move_index: int) -> str | None:
        idx = move_index * 2
        return self.solution_moves[idx] if idx < len(self.solution_moves) else None

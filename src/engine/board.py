"""Board state and rule API for Quoridor."""


class Board:
    """Represent the current state of a Quoridor board."""

    def make_move(self, move: object) -> None:
        """Apply a move to the board."""
        pass

    def undo_move(self, move: object) -> None:
        """Undo a previously applied move."""
        pass

    def get_legal_moves(self) -> list[object]:
        """Return all legal moves available in the current board state."""
        pass

    def is_game_over(self) -> bool:
        """Return whether the game has reached a terminal state."""
        pass

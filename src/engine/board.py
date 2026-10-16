"""Quoridor board state and move validation."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Literal

BOARD_SIZE = 9
Player = Literal[0, 1]
Orientation = Literal["horizontal", "vertical"]
Wall = tuple[Orientation, int, int]
Position = tuple[int, int]


@dataclass(frozen=True)
class Move:
    """A pawn destination or a wall anchor, using zero-based board coordinates."""

    kind: Literal["pawn", "wall"]
    x: int
    y: int
    orientation: Orientation | None = None

    @classmethod
    def pawn(cls, x: int, y: int) -> Move:
        """Create a pawn move to cell ``(x, y)``."""
        return cls("pawn", x, y)

    @classmethod
    def wall(cls, x: int, y: int, orientation: Orientation) -> Move:
        """Create a wall at anchor ``(x, y)``."""
        return cls("wall", x, y, orientation)


class Board:
    """Represent a two-player 9×9 Quoridor board.

    Player 0 starts at the bottom and wins by reaching row 0. Player 1 starts
    at the top and wins by reaching row 8. Wall anchors are zero-based and
    span two adjacent cells.
    """

    def __init__(self) -> None:
        self.pawns: list[Position] = [(4, 8), (4, 0)]
        self.walls_remaining = [10, 10]
        self.walls: set[Wall] = set()
        self.current_player: Player = 0
        self.winner: Player | None = None
        self._history: list[
            tuple[
                Move,
                list[Position],
                list[int],
                set[Wall],
                Player,
                Player | None,
            ]
        ] = []

    def make_move(self, move: Move) -> None:
        """Apply a legal pawn move or wall placement."""
        if not self.is_legal_move(move):
            raise ValueError(f"Illegal move: {move}")

        self._history.append(
            (
                move,
                self.pawns.copy(),
                self.walls_remaining.copy(),
                self.walls.copy(),
                self.current_player,
                self.winner,
            )
        )
        if move.kind == "pawn":
            self.pawns[self.current_player] = (move.x, move.y)
            goal_row = 0 if self.current_player == 0 else BOARD_SIZE - 1
            if move.y == goal_row:
                self.winner = self.current_player
        else:
            assert move.orientation is not None
            self.walls.add((move.orientation, move.x, move.y))
            self.walls_remaining[self.current_player] -= 1

        if self.winner is None:
            self.current_player = 1 if self.current_player == 0 else 0

    def undo_move(self, move: Move) -> None:
        """Undo the most recently applied move."""
        if not self._history or self._history[-1][0] != move:
            raise ValueError("Only the most recently applied move can be undone.")
        _, pawns, walls_remaining, walls, current_player, winner = self._history.pop()
        self.pawns = pawns
        self.walls_remaining = walls_remaining
        self.walls = walls
        self.current_player = current_player
        self.winner = winner

    def get_legal_moves(self) -> list[Move]:
        """Return every legal move for the player whose turn it is."""
        if self.is_game_over():
            return []
        moves = self.get_legal_pawn_moves()
        if self.walls_remaining[self.current_player] > 0:
            for orientation in ("horizontal", "vertical"):
                for y in range(BOARD_SIZE - 1):
                    for x in range(BOARD_SIZE - 1):
                        candidate = Move.wall(x, y, orientation)
                        if self._can_place_wall(orientation, x, y):
                            moves.append(candidate)
        return moves

    def get_legal_pawn_moves(self) -> list[Move]:
        """Return legal pawn destinations without enumerating wall placements."""
        if self.is_game_over():
            return []
        return [
            Move.pawn(x, y)
            for x, y in self._pawn_destinations(self.current_player)
        ]

    def is_legal_move(self, move: Move) -> bool:
        """Return whether ``move`` is legal in the current state."""
        if self.is_game_over():
            return False
        if move.kind == "pawn":
            return (move.x, move.y) in self._pawn_destinations(self.current_player)
        if move.kind == "wall" and move.orientation in ("horizontal", "vertical"):
            return self._can_place_wall(move.orientation, move.x, move.y)
        return False

    def is_game_over(self) -> bool:
        """Return whether either pawn has reached its goal row."""
        return self.winner is not None

    @property
    def last_move(self) -> Move | None:
        """Return the latest move, if one can be undone."""
        return self._history[-1][0] if self._history else None

    def _pawn_destinations(self, player: Player) -> set[Position]:
        position = self.pawns[player]
        opponent = self.pawns[1 - player]
        destinations: set[Position] = set()

        for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            adjacent = (position[0] + dx, position[1] + dy)
            if not self._inside(adjacent) or self._edge_blocked(position, adjacent):
                continue

            if adjacent != opponent:
                destinations.add(adjacent)
                continue

            jump = (opponent[0] + dx, opponent[1] + dy)
            if self._inside(jump) and not self._edge_blocked(opponent, jump):
                destinations.add(jump)
                continue

            for side_dx, side_dy in ((-dy, dx), (dy, -dx)):
                side = (opponent[0] + side_dx, opponent[1] + side_dy)
                if (
                    self._inside(side)
                    and side != position
                    and not self._edge_blocked(opponent, side)
                ):
                    destinations.add(side)
        return destinations

    def _can_place_wall(
        self,
        orientation: Orientation,
        x: int,
        y: int,
    ) -> bool:
        if (
            not 0 <= x < BOARD_SIZE - 1
            or not 0 <= y < BOARD_SIZE - 1
            or self.walls_remaining[self.current_player] <= 0
        ):
            return False

        for existing_orientation, existing_x, existing_y in self.walls:
            if existing_orientation != orientation and (existing_x, existing_y) == (x, y):
                return False
            if orientation == "horizontal":
                overlaps = existing_orientation == orientation and existing_y == y and abs(existing_x - x) <= 1
            else:
                overlaps = existing_orientation == orientation and existing_x == x and abs(existing_y - y) <= 1
            if overlaps:
                return False

        self.walls.add((orientation, x, y))
        paths_remain = all(self._has_path_to_goal(player) for player in (0, 1))
        self.walls.remove((orientation, x, y))
        return paths_remain

    def _has_path_to_goal(self, player: Player) -> bool:
        goal_row = 0 if player == 0 else BOARD_SIZE - 1
        queue = deque([self.pawns[player]])
        visited = {self.pawns[player]}

        while queue:
            current = queue.popleft()
            if current[1] == goal_row:
                return True
            for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
                neighbor = (current[0] + dx, current[1] + dy)
                if (
                    self._inside(neighbor)
                    and neighbor not in visited
                    and not self._edge_blocked(current, neighbor)
                ):
                    visited.add(neighbor)
                    queue.append(neighbor)
        return False

    def _edge_blocked(self, start: Position, end: Position) -> bool:
        for orientation, x, y in self.walls:
            if start[0] == end[0]:
                cell_x = start[0]
                lower_row = min(start[1], end[1])
                if orientation == "horizontal" and y == lower_row and x <= cell_x <= x + 1:
                    return True
            elif start[1] == end[1]:
                cell_y = start[1]
                left_column = min(start[0], end[0])
                if orientation == "vertical" and x == left_column and y <= cell_y <= y + 1:
                    return True
        return False

    @staticmethod
    def _inside(position: Position) -> bool:
        return 0 <= position[0] < BOARD_SIZE and 0 <= position[1] < BOARD_SIZE

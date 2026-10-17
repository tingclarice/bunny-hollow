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

    def __init__(self, time_limit_ms: int = 600000) -> None:
        self.pawns: list[Position] = [(4, 8), (4, 0)]
        self.walls_remaining = [10, 10]
        self.walls: set[Wall] = set()
        self.current_player: Player = 0
        self.winner: Player | None = None
        self.player_times_ms: list[int] = [0, 0]
        self.time_limit_ms: int = time_limit_ms
        self.cached_paths: list[list[Position] | None] = [
            self._has_path_to_goal(0),
            self._has_path_to_goal(1),
        ]
        self._history: list[
            tuple[
                Move,
                list[Position],
                list[int],
                set[Wall],
                Player,
                Player | None,
                list[list[Position] | None],
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
                [p.copy() if p is not None else None for p in self.cached_paths],
            )
        )
        if move.kind == "pawn":
            self.pawns[self.current_player] = (move.x, move.y)
            goal_row = 0 if self.current_player == 0 else BOARD_SIZE - 1
            if move.y == goal_row:
                self.winner = self.current_player
            self.cached_paths[self.current_player] = self._has_path_to_goal(self.current_player)
        else:
            assert move.orientation is not None
            self.walls.add((move.orientation, move.x, move.y))
            self.walls_remaining[self.current_player] -= 1
            for player in (0, 1):
                if self._wall_blocks_path(
                    move.orientation, move.x, move.y, self.cached_paths[player]
                ):
                    self.cached_paths[player] = self._has_path_to_goal(player)

        if self.winner is None:
            self.current_player = 1 if self.current_player == 0 else 0

    def undo_move(self, move: Move) -> None:
        """Undo the most recently applied move."""
        if not self._history or self._history[-1][0] != move:
            raise ValueError("Only the most recently applied move can be undone.")
        _, pawns, walls_remaining, walls, current_player, winner, cached_paths = (
            self._history.pop()
        )
        self.pawns = pawns
        self.walls_remaining = walls_remaining
        self.walls = walls
        self.current_player = current_player
        self.winner = winner
        self.cached_paths = cached_paths

    def tick_timer(self, player: Player, elapsed_ms: int) -> None:
        """Increment the active player's time and check for timeout."""
        self.player_times_ms[player] += elapsed_ms
        if self.player_times_ms[player] > self.time_limit_ms and self.winner is None:
            self.winner = 1 if player == 0 else 0

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
        """Return whether either pawn has reached its goal row or a player timed out."""
        if self.winner is not None:
            return True
        for player in (0, 1):
            if self.player_times_ms[player] > self.time_limit_ms:
                self.winner = 1 if player == 0 else 0
                return True
        return False

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

    @staticmethod
    def _wall_blocks_path(
        orientation: Orientation,
        x: int,
        y: int,
        path: list[Position] | None,
    ) -> bool:
        if not path or len(path) < 2:
            return True
        for i in range(len(path) - 1):
            c1 = path[i]
            c2 = path[i + 1]
            if orientation == "horizontal" and c1[0] == c2[0]:
                if y == min(c1[1], c2[1]) and x <= c1[0] <= x + 1:
                    return True
            elif orientation == "vertical" and c1[1] == c2[1]:
                if x == min(c1[0], c2[0]) and y <= c1[1] <= y + 1:
                    return True
        return False

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

        for player in (0, 1):
            cached = self.cached_paths[player]
            if not cached or cached[0] != self.pawns[player]:
                self.cached_paths[player] = self._has_path_to_goal(player)

        blocks_0 = self._wall_blocks_path(orientation, x, y, self.cached_paths[0])
        blocks_1 = self._wall_blocks_path(orientation, x, y, self.cached_paths[1])

        if not blocks_0 and not blocks_1:
            return True

        self.walls.add((orientation, x, y))
        p0_ok = (not blocks_0) or (self._has_path_to_goal(0) is not None)
        p1_ok = (not blocks_1) or (self._has_path_to_goal(1) is not None)
        self.walls.remove((orientation, x, y))
        return p0_ok and p1_ok

    def _has_path_to_goal(self, player: Player) -> list[Position] | None:
        goal_row = 0 if player == 0 else BOARD_SIZE - 1
        start = self.pawns[player]
        queue = deque([start])
        parent: dict[Position, Position | None] = {start: None}

        while queue:
            current = queue.popleft()
            if current[1] == goal_row:
                path: list[Position] = []
                curr: Position | None = current
                while curr is not None:
                    path.append(curr)
                    curr = parent[curr]
                path.reverse()
                return path
            for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
                neighbor = (current[0] + dx, current[1] + dy)
                if (
                    self._inside(neighbor)
                    and neighbor not in parent
                    and not self._edge_blocked(current, neighbor)
                ):
                    parent[neighbor] = current
                    queue.append(neighbor)
        return None

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

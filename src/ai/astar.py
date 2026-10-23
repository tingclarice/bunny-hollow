"""A* pathfinding for Quoridor board states."""

from __future__ import annotations

from heapq import heappop, heappush
from itertools import count

from src.engine.board import BOARD_SIZE, Board, Player, Position


def find_path(board: Board, player: Player) -> list[Position] | None:
    """Return the shortest wall-aware path from a player's pawn to its goal.

    The path is a list of board coordinates, including both the starting and
    goal positions. ``None`` is returned if no route to the goal exists.
    """
    if player not in (0, 1):
        raise ValueError(f"Invalid player: {player}")

    start = board.pawns[player]
    goal_row = 0 if player == 0 else BOARD_SIZE - 1

    def heuristic(position: Position) -> int:
        return abs(position[1] - goal_row)

    sequence = count()
    frontier: list[tuple[int, int, int, Position]] = [
        (heuristic(start), 0, next(sequence), start)
    ]
    cost_so_far: dict[Position, int] = {start: 0}
    parent: dict[Position, Position | None] = {start: None}

    while frontier:
        _, current_cost, _, current = heappop(frontier)
        if current_cost != cost_so_far[current]:
            continue

        if current[1] == goal_row:
            path: list[Position] = []
            position: Position | None = current
            while position is not None:
                path.append(position)
                position = parent[position]
            path.reverse()
            return path

        for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            neighbor = (current[0] + dx, current[1] + dy)
            if not board._inside(neighbor) or board._edge_blocked(current, neighbor):
                continue

            tentative_cost = current_cost + 1
            if tentative_cost >= cost_so_far.get(neighbor, float("inf")):
                continue

            cost_so_far[neighbor] = tentative_cost
            parent[neighbor] = current
            priority = tentative_cost + heuristic(neighbor)
            heappush(
                frontier,
                (priority, tentative_cost, next(sequence), neighbor),
            )

    return None

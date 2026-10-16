"""Tests for Quoridor GUI sprite direction selection."""

import pytest
import pygame

from src.gui.game import QuoridorGame


@pytest.mark.parametrize(
    ("current", "destination", "expected"),
    [
        ((4, 4), (4, 3), "up"),
        ((4, 4), (4, 5), "down"),
        ((4, 4), (3, 4), "left"),
        ((4, 4), (5, 4), "right"),
        ((4, 4), (4, 2), "up"),
        ((4, 4), (6, 4), "right"),
    ],
)
def test_bunny_facing_matches_last_move(
    current: tuple[int, int],
    destination: tuple[int, int],
    expected: str,
) -> None:
    assert QuoridorGame._direction_for_move(current, destination) == expected


@pytest.mark.parametrize(
    "destination",
    [
        (4, 4),
        (5, 3),
    ],
)
def test_bunny_facing_rejects_non_orthogonal_moves(
    destination: tuple[int, int],
) -> None:
    with pytest.raises(ValueError, match="one orthogonal square"):
        QuoridorGame._direction_for_move((4, 4), destination)


@pytest.mark.parametrize(
    ("width", "height"),
    [
        (1280, 800),
        (900, 650),
        (720, 480),
        (640, 480),
        (500, 350),
        (320, 300),
    ],
)
def test_responsive_layout_stays_inside_window(
    width: int,
    height: int,
) -> None:
    board, panel, _ = QuoridorGame._layout_for_size(width, height)
    window = pygame.Rect(0, 0, width, height)

    assert window.contains(board)
    assert window.contains(panel)
    assert not board.colliderect(panel)
    if width >= 720:
        assert panel.top == board.top
        assert panel.bottom == board.bottom
    else:
        assert panel.top >= board.bottom


def test_player_timers_only_advance_for_the_active_player() -> None:
    pygame.font.init()
    game = QuoridorGame()
    start = game.last_clock_update_ms

    game._update_timers(start + 1_250)
    game.board.current_player = 1
    game._update_timers(start + 1_750)

    assert game.player_times_ms == [1_250, 500]

    game.board.winner = 1
    game._update_timers(start + 2_250)
    assert game.player_times_ms == [1_250, 500]

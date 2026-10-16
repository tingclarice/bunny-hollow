"""Tests for core Quoridor board rules."""

import pytest

from src.engine.board import Board, Move


def test_pawn_move_updates_turn_and_position() -> None:
    board = Board()
    move = Move.pawn(4, 7)

    assert board.is_legal_move(move)
    board.make_move(move)

    assert board.pawns[0] == (4, 7)
    assert board.current_player == 1


def test_wall_blocks_movement_and_uses_one_wall() -> None:
    board = Board()
    move = Move.wall(4, 6, "horizontal")

    assert board.is_legal_move(move)
    board.make_move(move)

    assert ("horizontal", 4, 6) in board.walls
    assert board.walls_remaining == [9, 10]
    assert board._edge_blocked((4, 6), (4, 7))
    assert board.current_player == 1


def test_pawn_can_jump_over_opponent() -> None:
    board = Board()
    board.pawns = [(4, 4), (4, 3)]

    destinations = {(move.x, move.y) for move in board.get_legal_pawn_moves()}

    assert (4, 2) in destinations
    assert (4, 3) not in destinations


def test_blocked_jump_allows_side_step() -> None:
    board = Board()
    board.pawns = [(4, 4), (4, 3)]
    board.walls.add(("horizontal", 4, 2))

    destinations = {(move.x, move.y) for move in board.get_legal_pawn_moves()}

    assert (4, 2) not in destinations
    assert (3, 3) in destinations
    assert (5, 3) in destinations


def test_undo_restores_previous_state() -> None:
    board = Board()
    move = Move.wall(2, 3, "vertical")
    board.make_move(move)

    assert board.last_move == move
    board.undo_move(move)

    assert board.walls == set()
    assert board.walls_remaining == [10, 10]
    assert board.current_player == 0
    assert board.last_move is None


def test_illegal_move_is_rejected() -> None:
    board = Board()

    with pytest.raises(ValueError, match="Illegal move"):
        board.make_move(Move.pawn(4, 4))


def test_goal_move_ends_the_game() -> None:
    board = Board()
    board.pawns = [(4, 1), (3, 0)]

    board.make_move(Move.pawn(4, 0))

    assert board.is_game_over()
    assert board.winner == 0
    assert board.get_legal_moves() == []

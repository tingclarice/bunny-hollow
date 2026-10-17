"""Pygame interface for the first playable Quoridor milestone."""

from __future__ import annotations

from pathlib import Path

import pygame

from src.gui.assets import GameAssets
from src.gui.board_renderer import BoardRenderer
from src.gui.sidebar import SidebarRenderer, SidebarState
from src.gui.theme import (
    GARDEN_BACKGROUND_TILE_SIZE,
    OCEAN_COLOR,
    OCEAN_TILE,
    MOVE_DIRECTION_BY_DELTA,
    Direction,
    Position,
)
from src.engine.board import BOARD_SIZE, Board, Move, Orientation


class QuoridorGame:
    """Draw the board and handle local two-player input."""

    def __init__(self) -> None:
        self.board = Board()
        self.pawn_directions: list[Direction] = ["up", "down"]
        self._direction_history: list[list[Direction]] = []
        self._pawn_move_animations: dict[int, tuple[Position, Position, int]] = {}
        self.wall_mode = False
        self.wall_orientation: Orientation = "horizontal"
        self.message = "Choose a highlighted square to move."
        self.help_visible = False
        self.button_pressed: str | None = None
        self.button_pressed_until = 0
        self.player_times_ms = [0, 0]
        self.last_clock_update_ms = pygame.time.get_ticks()
        self.move_records: list[tuple[int, Move, Position | None]] = []
        self.window_size = (1100, 800)
        self.fullscreen = False
        asset_root = Path(__file__).resolve().parents[2] / "assets"
        self.assets = GameAssets(asset_root)
        self.board_renderer = BoardRenderer(self.assets)
        self.sidebar_renderer = SidebarRenderer(self.assets)
        self.board_rect = pygame.Rect(0, 0, 0, 0)
        self.wall_button = pygame.Rect(0, 0, 0, 0)
        self.restart_button = pygame.Rect(0, 0, 0, 0)
        self.help_button = pygame.Rect(0, 0, 0, 0)
        self.wall_orientation_button = pygame.Rect(0, 0, 0, 0)
        self.panel_rect = pygame.Rect(0, 0, 0, 0)

    def run(self) -> None:
        """Run the resizable 60 FPS game window."""
        screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
        pygame.display.set_caption("Bunny Hollow | Quoridor")
        clock = pygame.time.Clock()
        running = True

        while running:
            self._update_timers(pygame.time.get_ticks())
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE and not self.fullscreen:
                    self.window_size = event.size
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.help_visible:
                            self.help_visible = False
                        else:
                            running = False
                    elif event.key == pygame.K_F11:
                        self.fullscreen = not self.fullscreen
                        if self.fullscreen:
                            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                        else:
                            screen = pygame.display.set_mode(
                                self.window_size,
                                pygame.RESIZABLE,
                            )
                    elif event.key == pygame.K_n:
                        self._restart()
                    elif event.key == pygame.K_w:
                        self.wall_mode = not self.wall_mode
                    elif event.key == pygame.K_h:
                        self.help_visible = not self.help_visible
                    elif event.key == pygame.K_r:
                        self.wall_orientation = (
                            "vertical" if self.wall_orientation == "horizontal" else "horizontal"
                        )
                    elif event.key == pygame.K_BACKSPACE and self.board.last_move is not None:
                        last_move = self.board.last_move
                        previous_directions = self._direction_history.pop()
                        self.board.undo_move(last_move)
                        self.move_records.pop()
                        self.pawn_directions = previous_directions
                        self._pawn_move_animations.clear()
                        self.message = "Last move undone."
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.button_pressed = self._button_at(event.pos)
                    self.button_pressed_until = pygame.time.get_ticks() + 140
                    self._handle_click(event.pos)

            screen.fill(OCEAN_COLOR)
            self._draw(screen)
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

    def _draw(self, screen: pygame.Surface) -> None:
        width, height = screen.get_size()
        self._draw_tiled_texture(
            screen,
            self._tile_surface(*OCEAN_TILE, GARDEN_BACKGROUND_TILE_SIZE),
            screen.get_rect(),
        )
        gap = max(2, min(4, round(height * 0.004)))
        self.board_rect, self.panel_rect, compact_panel = self._layout_for_size(width, height)
        self.board_renderer.set_layout(self.board_rect, gap)
        self.board_renderer.draw(
            screen,
            self.board,
            self.move_records,
            self.wall_mode,
            self.wall_orientation,
            self.pawn_directions,
            self._pawn_move_animations,
        )
        self._draw_panel(screen, self.panel_rect, compact_panel)

    @staticmethod
    def _layout_for_size(
        width: int,
        height: int,
    ) -> tuple[pygame.Rect, pygame.Rect, bool]:
        if width >= 720:
            panel_width = max(230, min(310, round(width * 0.28)))
            spacing = 18
            margin = 16
            board_size = max(
                180,
                min(650, height - 32, width - 2 * margin - spacing - panel_width),
            )
            group_width = board_size + spacing + panel_width
            board_x = max(margin, (width - group_width) // 2)
            board_y = max(12, (height - board_size) // 2)
            board = pygame.Rect(board_x, board_y, board_size, board_size)
            panel = pygame.Rect(
                board.right + spacing,
                board.top,
                panel_width,
                board_size,
            )
            return board, panel, board_size < 440

        margin = 12
        spacing = 10
        panel_width = max(180, width - margin * 2)
        desired_panel_height = min(190, max(130, round(height * 0.30)))
        board_size = max(
            140,
            min(460, panel_width, height - margin * 2 - spacing - desired_panel_height),
        )
        board_x = (width - board_size) // 2
        board_y = margin
        board = pygame.Rect(board_x, board_y, board_size, board_size)
        panel_y = board.bottom + spacing
        panel_height = max(112, height - panel_y - margin)
        panel = pygame.Rect(margin, panel_y, panel_width, panel_height)
        return board, panel, True

    def _draw_panel(
        self,
        screen: pygame.Surface,
        panel: pygame.Rect,
        compact: bool,
    ) -> None:
        self.panel_rect = panel
        self.wall_button, self.restart_button, self.help_button = (
            self.sidebar_renderer.draw(
                screen,
                panel,
                compact,
                SidebarState(
                    board=self.board,
                    wall_mode=self.wall_mode,
                    wall_orientation=self.wall_orientation,
                    help_visible=self.help_visible,
                    player_times_ms=self.player_times_ms,
                    button_pressed=self.button_pressed,
                    button_pressed_until=self.button_pressed_until,
                ),
            )
        )

    def _handle_click(self, position: tuple[int, int]) -> None:
        if self.restart_button.collidepoint(position):
            self._restart()
            return
        if self.help_button.collidepoint(position):
            self.help_visible = not self.help_visible
            return
        if self.wall_button.collidepoint(position):
            self.wall_mode = not self.wall_mode
            return
        if not self.board_rect.collidepoint(position) or self.board.is_game_over():
            return

        if self.wall_mode:
            x, y = self._wall_anchor(position)
            move = Move.wall(x, y, self.wall_orientation)
            if self.board.is_legal_move(move):
                player = self.board.current_player
                self._direction_history.append(self.pawn_directions.copy())
                self.board.make_move(move)
                self.move_records.append((player, move, None))
                self.wall_mode = False
                self.message = "Wall placed. Your opponent's turn."
            else:
                self.message = "That wall placement is not legal."
            return

        for move in self.board.get_legal_pawn_moves():
            if self._cell_rect(move.x, move.y).collidepoint(position):
                player = self.board.current_player
                start = self.board.pawns[player]
                destination = (move.x, move.y)
                direction = self._direction_for_move(start, destination)
                self._direction_history.append(self.pawn_directions.copy())
                self.pawn_directions[player] = direction
                self.board.make_move(move)
                self.move_records.append((player, move, start))
                self._pawn_move_animations[player] = (
                    start,
                    destination,
                    pygame.time.get_ticks(),
                )
                self.message = "Move made. Your opponent's turn."
                return
        self.message = "Choose a highlighted square to move."

    def _wall_anchor(self, position: tuple[int, int]) -> tuple[int, int]:
        return self.board_renderer.wall_anchor(position)

    def _cell_rect(self, x: int, y: int) -> pygame.Rect:
        return self.board_renderer.cell_rect(x, y)

    def _wall_rect(self, x: int, y: int, orientation: Orientation) -> pygame.Rect:
        return self.board_renderer.wall_rect(x, y, orientation)

    def _tile_surface(self, tile_x: int, tile_y: int, size: int) -> pygame.Surface:
        return self.assets.tile_surface(tile_x, tile_y, size)

    @staticmethod
    def _draw_tiled_texture(
        screen: pygame.Surface,
        texture: pygame.Surface,
        destination: pygame.Rect,
    ) -> None:
        tile_width, tile_height = texture.get_size()
        for y in range(destination.top, destination.bottom, tile_height):
            for x in range(destination.left, destination.right, tile_width):
                width = min(tile_width, destination.right - x)
                height = min(tile_height, destination.bottom - y)
                screen.blit(texture, (x, y), pygame.Rect(0, 0, width, height))

    def _button_at(self, position: tuple[int, int]) -> str | None:
        if self.wall_button.collidepoint(position):
            return "wall"
        if self.restart_button.collidepoint(position):
            return "restart"
        if self.help_button.collidepoint(position):
            return "help"
        return None

    def _restart(self) -> None:
        self.board = Board()
        self.pawn_directions = ["up", "down"]
        self._direction_history.clear()
        self.move_records.clear()
        self.player_times_ms = [0, 0]
        self.last_clock_update_ms = pygame.time.get_ticks()
        self._pawn_move_animations.clear()
        self.wall_mode = False
        self.wall_orientation = "horizontal"
        self.help_visible = False
        self.button_pressed = None
        self.message = "Choose a highlighted square to move."

    def _update_timers(self, now: int) -> None:
        elapsed = max(0, now - self.last_clock_update_ms)
        if not self.board.is_game_over():
            self.player_times_ms[self.board.current_player] += elapsed
        self.last_clock_update_ms = now

    @staticmethod
    def _direction_for_move(current: Position, destination: Position) -> Direction:
        delta = (destination[0] - current[0], destination[1] - current[1])
        if delta in MOVE_DIRECTION_BY_DELTA:
            return MOVE_DIRECTION_BY_DELTA[delta]
        if delta[0] == 0 and abs(delta[1]) == 2:
            return "down" if delta[1] > 0 else "up"
        if delta[1] == 0 and abs(delta[0]) == 2:
            return "right" if delta[0] > 0 else "left"
        if delta[1] != 0:
            return "down" if delta[1] > 0 else "up"
        return "right" if delta[0] > 0 else "left"

"""Pygame interface for the first playable Quoridor milestone."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import pygame

from src.engine.board import BOARD_SIZE, Board, Move, Orientation

OCEAN_COLOR = (83, 161, 194)
PANEL = (248, 235, 210)
PANEL_SHADOW = (75, 49, 39)
PANEL_BORDER = (111, 72, 53)
PANEL_INSET = (218, 185, 137)
TEXT = (71, 51, 43)
MUTED = (126, 100, 77)
WALL_COLOR = (94, 62, 43)
PLAYER_COLORS = ((184, 75, 53), (43, 105, 134))
PLAYER_CARD_FILL = (255, 245, 218)
PLAYER_CARD_INACTIVE = (235, 220, 192)
PLAYER_CARD_MUTED = (145, 127, 108)
HIGHLIGHT = (255, 223, 78)
HIGHLIGHT_OUTLINE = (62, 50, 30)
FENCE_COLOR = (138, 83, 54)
FENCE_USED = (191, 171, 140)
SPRITE_SIZE = 48
SPRITE_COLUMNS = 8
SPRITE_ROWS = 4
PAWN_MOVE_ANIMATION_MS = 180
PAWN_SPRITE_CELL_SCALE = 2.7
Direction = Literal["up", "down", "left", "right"]
Position = tuple[int, int]
MOVE_DIRECTION_BY_DELTA: dict[Position, Direction] = {
    (0, -1): "up",
    (0, 1): "down",
    (-1, 0): "left",
    (1, 0): "right",
}
SPRITE_ROW_BY_DIRECTION: dict[Direction, int] = {
    "up": 0,
    "down": 1,
    "left": 2,
    "right": 3,
}
TILESET_TILE_SIZE = 16
GARDEN_GRASS_CENTER = (10, 3)
GARDEN_GRASS_TOP_LEFT = (9, 1)
GARDEN_GRASS_TOP = (11, 1)
GARDEN_GRASS_TOP_RIGHT = (12, 1)
GARDEN_GRASS_LEFT = (9, 2)
GARDEN_GRASS_RIGHT = (12, 3)
GARDEN_GRASS_BOTTOM_LEFT = (9, 4)
GARDEN_GRASS_BOTTOM = (10, 4)
GARDEN_GRASS_BOTTOM_RIGHT = (12, 4)
GARDEN_DIRT = (16, 2)
OCEAN_TILE = (13, 1)
GARDEN_BACKGROUND_TILE_SIZE = 32
GOAL_HOUSE_SPRITE_RECTS = ((256, 80, 16, 16), (256, 272, 16, 16))


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
        font_dir = asset_root / "Tileset" / "fonts"
        self.pixel_font = pygame.font.Font(str(font_dir / "PixelifySans-Regular.ttf"), 18)
        self.pixel_bold_font = pygame.font.Font(str(font_dir / "PixelifySans-Bold.ttf"), 24)
        self.pixel_small_font = pygame.font.Font(str(font_dir / "PixelifySans-Regular.ttf"), 14)
        sprite_sheet = pygame.image.load(str(asset_root / "Bunny_Run.png"))
        if sprite_sheet.get_size() != (SPRITE_SIZE * SPRITE_COLUMNS, SPRITE_SIZE * SPRITE_ROWS):
            raise ValueError(f"Unexpected bunny sprite sheet size: {sprite_sheet.get_size()}")
        self.bunny_frames = [
            [
                sprite_sheet.subsurface(
                    (column * SPRITE_SIZE, row * SPRITE_SIZE, SPRITE_SIZE, SPRITE_SIZE)
                ).copy()
                for column in range(SPRITE_COLUMNS)
            ]
            for row in range(SPRITE_ROWS)
        ]
        tileset_path = asset_root / "Tileset" / "Autotile_Grass_and_Dirt_Path_Tileset.png"
        self.tileset = pygame.image.load(str(tileset_path))
        self._scaled_tiles: dict[tuple[int, int, int], pygame.Surface] = {}
        house_tileset = pygame.image.load(str(asset_root / "Tileset" / "House_Tileset.png"))
        self.goal_house_sprites = [
            self._recolor_goal_house(house_tileset.subsurface(rect), player)
            for player, rect in enumerate(GOAL_HOUSE_SPRITE_RECTS)
        ]
        self.board_rect = pygame.Rect(0, 0, 0, 0)
        self.cell_size = 0.0
        self.gap = 0.0
        self.stride = 0.0
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
            self._tile_surface(*OCEAN_TILE, GARDEN_BACKGROUND_TILE_SIZE            ),
            screen.get_rect(),
        )
        gap = max(2, min(4, round(height * 0.004)))
        self.board_rect, self.panel_rect, compact_panel = self._layout_for_size(width, height)
        self.gap = gap
        board_size = self.board_rect.width
        self.cell_size = (board_size - gap * (BOARD_SIZE - 1)) / BOARD_SIZE
        self.stride = self.cell_size + gap

        corner_radius = max(8, round(self.cell_size * 0.22))
        pygame.draw.rect(screen, PANEL_SHADOW, self.board_rect, border_radius=corner_radius)
        self._draw_rounded_tiled_texture(
            screen,
            self._tile_surface(*GARDEN_DIRT, GARDEN_BACKGROUND_TILE_SIZE),
            self.board_rect,
            corner_radius,
        )
        pygame.draw.rect(
            screen,
            PANEL_BORDER,
            self.board_rect,
            width=2,
            border_radius=corner_radius,
        )
        self._draw_tiles(screen)
        self._draw_walls(screen)
        self._draw_wall_preview(screen)
        self._draw_pawns(screen)
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

    def _draw_tiles(self, screen: pygame.Surface) -> None:
        legal_destinations = {
            (move.x, move.y) for move in self.board.get_legal_pawn_moves()
        }
        for y in range(BOARD_SIZE):
            for x in range(BOARD_SIZE):
                rect = self._cell_rect(x, y)
                tile_x, tile_y = self._garden_tile_for_cell(x, y)
                screen.blit(self._tile_surface(tile_x, tile_y, rect.width), rect)
                goal_player = 0 if y == 0 else 1 if y == BOARD_SIZE - 1 else None
                if goal_player is not None and x == 0:
                    self._draw_goal_house(screen, rect, goal_player)
                last_entry = self.move_records[-1] if self.move_records else None
                if (
                    last_entry is not None
                    and last_entry[1].kind == "pawn"
                    and last_entry[2] == (x, y)
                ):
                    self._draw_last_move_cell(screen, rect, last_entry[0])
                if (x, y) in legal_destinations and not self.wall_mode:
                    pulse = (pygame.time.get_ticks() % 1200) / 1200
                    pulse_scale = 0.9 + 0.1 * (1 - abs(2 * pulse - 1))
                    radius = max(4, round(self.cell_size * 0.105 * pulse_scale))
                    dot_size = radius * 2 + 4
                    dot = pygame.Surface((dot_size, dot_size), pygame.SRCALPHA)
                    dot_center = (dot_size // 2, dot_size // 2)
                    pygame.draw.circle(dot, (*HIGHLIGHT_OUTLINE, 115), dot_center, radius + 2)
                    pygame.draw.circle(dot, (*HIGHLIGHT, 155), dot_center, radius)
                    screen.blit(dot, dot.get_rect(center=rect.center))

    def _draw_last_move_cell(
        self,
        screen: pygame.Surface,
        rect: pygame.Rect,
        player: int,
    ) -> None:
        tint = pygame.Surface(rect.size, pygame.SRCALPHA)
        tint.fill((*PLAYER_COLORS[player], 48))
        screen.blit(tint, rect)

    def _draw_goal_house(
        self,
        screen: pygame.Surface,
        rect: pygame.Rect,
        player: int,
    ) -> None:
        size = max(10, round(self.cell_size * 0.72))
        size = min(size, rect.width - 6, rect.height - 6)
        house = pygame.transform.scale(self.goal_house_sprites[player], (size, size))
        screen.blit(house, house.get_rect(center=rect.center))

    def _draw_walls(self, screen: pygame.Surface) -> None:
        for orientation, x, y in self.board.walls:
            rect = self._wall_rect(x, y, orientation)
            pygame.draw.rect(screen, (65, 45, 34), rect.move(1, 3), border_radius=5)
            pygame.draw.rect(screen, WALL_COLOR, rect, border_radius=5)
            shine = rect.inflate(-max(3, int(self.gap * 0.45)), -max(3, int(self.gap * 0.45)))
            if shine.width > 0 and shine.height > 0:
                pygame.draw.rect(screen, (133, 95, 65), shine, border_radius=3)
            if self.move_records and self.move_records[-1][1] == Move.wall(x, y, orientation):
                pygame.draw.rect(
                    screen,
                    HIGHLIGHT,
                    rect.inflate(4, 4),
                    width=max(2, round(self.gap)),
                )

    def _draw_wall_preview(self, screen: pygame.Surface) -> None:
        if not self.wall_mode or self.board.is_game_over():
            return
        mouse_position = pygame.mouse.get_pos()
        if not self.board_rect.collidepoint(mouse_position):
            return
        x, y = self._wall_anchor(mouse_position)
        move = Move.wall(x, y, self.wall_orientation)
        color = PLAYER_COLORS[self.board.current_player] if self.board.is_legal_move(move) else (210, 70, 66)
        rect = self._wall_rect(x, y, self.wall_orientation)
        preview = pygame.Surface(rect.size, pygame.SRCALPHA)
        preview.fill((*color, 145))
        screen.blit(preview, rect)
        pygame.draw.rect(screen, (*color, 235), rect, width=max(2, round(self.gap)))

    def _draw_pawns(self, screen: pygame.Surface) -> None:
        now = pygame.time.get_ticks()
        for player, position in enumerate(self.board.pawns):
            center = self._cell_rect(*position).center
            animation = self._pawn_move_animations.get(player)
            frame_index = 0
            if animation is not None:
                start, destination, started_at = animation
                elapsed = now - started_at
                if destination == position and elapsed < PAWN_MOVE_ANIMATION_MS:
                    progress = max(0.0, elapsed / PAWN_MOVE_ANIMATION_MS)
                    start_center = self._cell_rect(*start).center
                    end_center = self._cell_rect(*destination).center
                    center = (
                        round(start_center[0] + (end_center[0] - start_center[0]) * progress),
                        round(start_center[1] + (end_center[1] - start_center[1]) * progress),
                    )
                    frame_index = min(SPRITE_COLUMNS - 1, int(progress * SPRITE_COLUMNS))

            direction_row = SPRITE_ROW_BY_DIRECTION[self.pawn_directions[player]]
            frame = self.bunny_frames[direction_row][frame_index]
            frame_size = max(1, round(self.cell_size * PAWN_SPRITE_CELL_SCALE))
            scaled_frame = pygame.transform.scale(frame, (frame_size, frame_size))
            screen.blit(
                scaled_frame,
                scaled_frame.get_rect(
                    center=center
                ),
            )

    def _draw_panel(
        self,
        screen: pygame.Surface,
        panel: pygame.Rect,
        compact: bool,
    ) -> None:
        self.panel_rect = panel
        pygame.draw.rect(screen, PANEL_SHADOW, panel.move(4, 4))
        pygame.draw.rect(screen, PANEL_BORDER, panel)
        inner = panel.inflate(-6, -6)
        pygame.draw.rect(screen, PANEL, inner)
        pygame.draw.rect(screen, PANEL_INSET, inner.inflate(-6, -6), width=1)

        left = inner.x + 14
        right = inner.right - 14
        current = self.board.current_player
        winner = self.board.winner
        turn_text = (
            f"PLAYER {winner + 1} WINS!"
            if winner is not None
            else f"PLAYER {current + 1}'S TURN"
        )
        turn_player = winner if winner is not None else current
        if compact:
            self._draw_compact_panel(
                screen,
                inner,
                left,
                right,
                turn_text,
                turn_player,
            )
            return

        self._text(screen, "BUNNY HOLLOW", self.pixel_bold_font, TEXT, (left, inner.y + 10))
        self._text(screen, "GARDEN QUORIDOR", self.pixel_small_font, MUTED, (left + 1, inner.y + 39))
        pygame.draw.line(screen, PANEL_INSET, (left, inner.y + 61), (right, inner.y + 61), 2)
        if winner is not None:
            self._text(
                screen,
                f"PLAYER {winner + 1} WINS!",
                self.pixel_small_font,
                PLAYER_COLORS[winner],
                (left, inner.y + 66),
            )
        self._draw_player_cards(screen, left, right, inner.y + 82, 84, compact=False)
        button_x = left
        button_width = right - left
        self.wall_button = pygame.Rect(button_x, inner.y + 178, button_width, 36)
        self.restart_button = pygame.Rect(button_x, inner.y + 223, button_width, 34)
        self.help_button = pygame.Rect(button_x, inner.y + 266, button_width, 32)
        self._draw_wall_mode_toggle(screen, self.wall_button)
        self._draw_button(
            screen,
            self.restart_button,
            "NEW GAME  [N]",
            pressed=self._button_is_pressed("restart"),
        )
        self._draw_button(
            screen,
            self.help_button,
            "HELP  [H]",
            active=self.help_visible,
            pressed=self._button_is_pressed("help"),
        )

        if self.help_visible:
            help_lines = (
                "CLICK A BRIGHT DOT TO MOVE",
                "W: WALL MODE   R: ROTATE",
                "CLICK BOARD: PLACE WALL",
                "BACKSPACE: UNDO   N: NEW",
                "F11: FULLSCREEN   ESC: QUIT",
            )
            for index, line in enumerate(help_lines):
                self._fitted_text(
                    screen,
                    line,
                    self.pixel_small_font,
                    TEXT,
                    (left, inner.y + 310 + index * 16),
                    right - left,
                )
        else:
            self._fitted_text(
                screen,
                "DOT: MOVE  H: HELP",
                self.pixel_small_font,
                MUTED,
                (left, inner.bottom - 25),
                right - left,
            )

    def _draw_compact_panel(
        self,
        screen: pygame.Surface,
        inner: pygame.Rect,
        left: int,
        right: int,
        turn_text: str,
        turn_player: int,
    ) -> None:
        self._text(screen, "BUNNY HOLLOW", self.pixel_font, TEXT, (left, inner.y + 3))
        if "WINS" in turn_text:
            self._text(
                screen,
                f"P{turn_player + 1} WINS!",
                self.pixel_small_font,
                PLAYER_COLORS[turn_player],
                (left, inner.y + 23),
            )
        self._draw_player_cards(screen, left, right, inner.y + 27, 61, compact=True)

        button_gap = 5
        button_y = inner.y + 92
        button_height = 25
        button_width = max(44, (right - left - button_gap * 2) // 3)
        self.wall_button = pygame.Rect(left, button_y, button_width, button_height)
        self.restart_button = pygame.Rect(
            self.wall_button.right + button_gap,
            button_y,
            button_width,
            button_height,
        )
        self.help_button = pygame.Rect(
            self.restart_button.right + button_gap,
            button_y,
            right - self.restart_button.right - button_gap,
            button_height,
        )
        self._draw_wall_mode_toggle(screen, self.wall_button, compact=True)
        self._draw_button(
            screen,
            self.restart_button,
            "NEW",
            pressed=self._button_is_pressed("restart"),
            compact=True,
        )
        self._draw_button(
            screen,
            self.help_button,
            "HELP",
            active=self.help_visible,
            pressed=self._button_is_pressed("help"),
            compact=True,
        )
        if inner.height >= 185:
            help_top = button_y + button_height + 9
            if self.help_visible:
                self._draw_compact_help(
                    screen,
                    pygame.Rect(left, help_top, right - left, inner.bottom - help_top - 22),
                )
            else:
                self._fitted_text(
                    screen,
                    "W: WALL MODE  R: ROTATE  BACKSPACE: UNDO",
                    self.pixel_small_font,
                    MUTED,
                    (left, help_top),
                    right - left,
                )
        else:
            if inner.height >= 125:
                hint = "W WALL  R ROTATE  N NEW  H CLOSE" if self.help_visible else (
                    "WALL: R ROTATES  |  H: HELP"
                    if self.wall_mode
                    else "DOT: MOVE  H: HELP"
                )
                self._fitted_text(
                    screen,
                    hint,
                    self.pixel_small_font,
                    MUTED,
                    (left, inner.bottom - 18),
                    right - left,
                )

    def _draw_compact_help(self, screen: pygame.Surface, rect: pygame.Rect) -> None:
        pygame.draw.rect(screen, PANEL_INSET, rect, width=1)
        lines = (
            "DOT: MOVE",
            "W: WALL MODE  R: ROTATE",
            "BACKSPACE: UNDO",
            "N: NEW GAME  ESC: CLOSE",
        )
        for index, line in enumerate(lines):
            self._fitted_text(
                screen,
                line,
                self.pixel_small_font,
                TEXT,
                (rect.x + 6, rect.y + 5 + index * 16),
                rect.width - 12,
            )

    def _draw_wall_mode_toggle(
        self,
        screen: pygame.Surface,
        rect: pygame.Rect,
        *,
        compact: bool = False,
    ) -> None:
        active = self.wall_mode
        selected_color = PLAYER_COLORS[self.board.current_player]
        face = (
            tuple((channel + 255) // 2 for channel in selected_color)
            if active
            else (232, 209, 170)
        )
        frame = rect.move(0, 2) if self._button_is_pressed("wall") else rect
        pygame.draw.rect(screen, PANEL_SHADOW, rect.move(0, 3))
        pygame.draw.rect(
            screen,
            selected_color if active else PANEL_BORDER,
            frame,
            width=3 if active else 1,
        )
        pygame.draw.rect(screen, face, frame.inflate(-4, -4))
        label = ("W ON" if active else "W OFF") if compact else (
            "WALL MODE  ON" if active else "WALL MODE  OFF"
        )
        font = self.pixel_small_font if compact else self.pixel_font
        label_image = font.render(label, True, TEXT)
        label_rect = label_image.get_rect(
            midleft=(frame.left + 7, frame.centery),
        )
        screen.blit(label_image, label_rect)

        icon_width = 14 if compact else 20
        icon_height = 5 if compact else 6
        icon_center_x = frame.right - (14 if compact else 22)
        icon_center_y = frame.centery
        if self.wall_orientation == "horizontal":
            icon = pygame.Rect(
                icon_center_x - icon_width // 2,
                icon_center_y - icon_height // 2,
                icon_width,
                icon_height,
            )
        else:
            icon = pygame.Rect(
                icon_center_x - icon_height // 2,
                icon_center_y - icon_width // 2,
                icon_height,
                icon_width,
            )
        pygame.draw.rect(screen, selected_color if active else TEXT, icon)

    def _draw_player_cards(
        self,
        screen: pygame.Surface,
        left: int,
        right: int,
        y: int,
        height: int,
        *,
        compact: bool = False,
    ) -> None:
        gap = 6
        card_width = (right - left - gap) // 2
        for player in (0, 1):
            card = pygame.Rect(left + player * (card_width + gap), y, card_width, height)
            active_player = (
                self.board.winner
                if self.board.winner is not None
                else self.board.current_player
            )
            active = player == active_player
            fill = PLAYER_CARD_FILL if active else PLAYER_CARD_INACTIVE
            border_width = 4 if active else 1
            if active:
                glow = card.inflate(4, 4)
                glow_color = tuple(min(255, channel + 38) for channel in PLAYER_COLORS[player])
                pygame.draw.rect(screen, glow_color, glow, width=2)
                pygame.draw.rect(screen, PLAYER_COLORS[player], card, width=border_width)
            else:
                pygame.draw.rect(screen, PLAYER_COLORS[player], card, width=border_width)
            pygame.draw.rect(screen, fill, card.inflate(-border_width * 2, -border_width * 2))

            portrait_size = 24 if compact else 40
            portrait_source = self.bunny_frames[
                SPRITE_ROW_BY_DIRECTION["down" if player == 0 else "up"]
            ][0]
            portrait_bounds = portrait_source.get_bounding_rect()
            portrait_source = portrait_source.subsurface(portrait_bounds)
            portrait = pygame.transform.scale(portrait_source, (portrait_size, portrait_size))
            portrait_rect = pygame.Rect(
                card.x + 5,
                card.y + 4,
                portrait_size,
                portrait_size,
            )
            screen.blit(portrait, portrait_rect)

            text_x = portrait_rect.right + 5
            text_color = TEXT if active else PLAYER_CARD_MUTED
            self._text(
                screen,
                f"P{player + 1}",
                self.pixel_small_font,
                text_color,
                (text_x, card.y + 2),
            )
            remaining = self.board.walls_remaining[player]
            self._text(
                screen,
                f"{remaining}/10",
                self.pixel_small_font,
                text_color,
                (text_x, card.y + (18 if compact else 21)),
            )
            timer_y = card.y + (33 if compact else 40)
            timer_color = PLAYER_COLORS[player] if active else PLAYER_CARD_MUTED
            self._draw_clock_icon(screen, text_x + 4, timer_y + 7, timer_color)
            self._text(
                screen,
                self._format_time(self.player_times_ms[player]),
                self.pixel_small_font,
                timer_color,
                (text_x + 12, timer_y),
            )

            slots_y = card.bottom - (8 if compact else 15)
            slot_width = max(3, min(8, (card.width - 14) // 13))
            slot_gap = max(1, (card.width - 14 - slot_width * 10) // 9)
            slots_width = slot_width * 10 + slot_gap * 9
            slots_x = card.centerx - slots_width // 2
            for slot in range(10):
                slot_rect = pygame.Rect(
                    slots_x + slot * (slot_width + slot_gap),
                    slots_y,
                    slot_width,
                    6 if compact else 9,
                )
                if slot < remaining:
                    slot_color = (
                        PLAYER_COLORS[player]
                        if active
                        else tuple(
                            (channel + muted_channel * 2) // 3
                            for channel, muted_channel in zip(
                                PLAYER_COLORS[player],
                                PLAYER_CARD_MUTED,
                            )
                        )
                    )
                    pygame.draw.rect(screen, slot_color, slot_rect)
                    pygame.draw.rect(screen, PANEL_BORDER, slot_rect, width=1)
                else:
                    pygame.draw.rect(screen, PANEL_INSET, slot_rect, width=1)

    @staticmethod
    def _draw_clock_icon(
        screen: pygame.Surface,
        center_x: int,
        center_y: int,
        color: tuple[int, int, int],
    ) -> None:
        pygame.draw.rect(screen, color, (center_x - 4, center_y - 4, 9, 9), width=1)
        pygame.draw.line(screen, color, (center_x, center_y - 2), (center_x, center_y))
        pygame.draw.line(screen, color, (center_x, center_y), (center_x + 2, center_y + 1))

    @staticmethod
    def _format_time(milliseconds: int) -> str:
        total_seconds = milliseconds // 1000
        return f"{total_seconds // 60:02}:{total_seconds % 60:02}"

    @staticmethod
    def _recolor_goal_house(source: pygame.Surface, player: int) -> pygame.Surface:
        sprite = source.copy()
        target = PLAYER_COLORS[player]
        for y in range(sprite.get_height()):
            for x in range(sprite.get_width()):
                red, green, blue, alpha = sprite.get_at((x, y))
                if red > green * 1.15 and red > blue * 1.15:
                    scale = max(red, green, blue) / 242
                elif green > red * 1.08 and green > blue * 0.98:
                    scale = max(red, green, blue) / 221
                else:
                    continue
                sprite.set_at(
                    (x, y),
                    (*tuple(min(255, round(channel * scale)) for channel in target), alpha),
                )
        return sprite

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
        offset_x = self.gap / 2
        offset_y = self.gap / 2
        x = round((position[0] - self.board_rect.left - self.stride + offset_x) / self.stride)
        y = round((position[1] - self.board_rect.top - self.stride + offset_y) / self.stride)
        return x, y

    def _cell_rect(self, x: int, y: int) -> pygame.Rect:
        return pygame.Rect(
            round(self.board_rect.left + x * self.stride),
            round(self.board_rect.top + y * self.stride),
            round(self.cell_size),
            round(self.cell_size),
        )

    def _wall_rect(self, x: int, y: int, orientation: Orientation) -> pygame.Rect:
        left = self.board_rect.left + x * self.stride
        top = self.board_rect.top + y * self.stride
        if orientation == "horizontal":
            return pygame.Rect(
                round(left),
                round(top + self.stride - self.gap / 2),
                round(2 * self.cell_size + self.gap),
                max(5, round(self.gap * 0.8)),
            )
        return pygame.Rect(
            round(left + self.stride - self.gap / 2),
            round(top),
            max(5, round(self.gap * 0.8)),
            round(2 * self.cell_size + self.gap),
        )

    def _tile_surface(self, tile_x: int, tile_y: int, size: int) -> pygame.Surface:
        key = (tile_x, tile_y, size)
        if key not in self._scaled_tiles:
            tile_rect = pygame.Rect(
                tile_x * TILESET_TILE_SIZE,
                tile_y * TILESET_TILE_SIZE,
                TILESET_TILE_SIZE,
                TILESET_TILE_SIZE,
            )
            tile = self.tileset.subsurface(tile_rect)
            self._scaled_tiles[key] = pygame.transform.scale(tile, (size, size))
        return self._scaled_tiles[key]

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

    @classmethod
    def _draw_rounded_tiled_texture(
        cls,
        screen: pygame.Surface,
        texture: pygame.Surface,
        destination: pygame.Rect,
        radius: int,
    ) -> None:
        layer = pygame.Surface(destination.size, pygame.SRCALPHA)
        cls._draw_tiled_texture(layer, texture, layer.get_rect())
        mask = pygame.Surface(destination.size, pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius)
        layer.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(layer, destination)

    @staticmethod
    def _draw_fence_icon(
        screen: pygame.Surface,
        x: int,
        y: int,
        *,
        active: bool,
    ) -> None:
        wood = FENCE_COLOR if active else FENCE_USED
        outline = PANEL_SHADOW if active else (157, 139, 115)
        pygame.draw.rect(screen, wood, (x + 2, y + 4, 9, 7))
        pygame.draw.rect(screen, outline, (x + 1, y + 1, 3, 12))
        pygame.draw.rect(screen, outline, (x + 9, y + 1, 3, 12))
        pygame.draw.rect(screen, outline, (x, y + 5, 13, 2))
        pygame.draw.rect(screen, PANEL_INSET if active else PANEL, (x + 1, y, 3, 2))
        pygame.draw.rect(screen, PANEL_INSET if active else PANEL, (x + 9, y, 3, 2))

    def _draw_button(
        self,
        screen: pygame.Surface,
        rect: pygame.Rect,
        label: str,
        *,
        active: bool = False,
        pressed: bool = False,
        compact: bool = False,
    ) -> None:
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        down = pressed and hovered
        if active:
            face = tuple(
                (channel + 255) // 2
                for channel in PLAYER_COLORS[self.board.current_player]
            )
        else:
            face = (255, 245, 218) if hovered else (232, 209, 170)
        frame = rect.move(0, 2) if down else rect
        pygame.draw.rect(screen, PANEL_SHADOW, rect.move(0, 3))
        pygame.draw.rect(screen, PANEL_BORDER, frame)
        pygame.draw.rect(screen, face, frame.inflate(-4, -4))
        if active:
            selected_color = PLAYER_COLORS[self.board.current_player]
            pygame.draw.rect(screen, selected_color, frame.inflate(-2, -2), width=2)
        font = self.pixel_small_font if compact else self.pixel_font
        self._center_text(screen, label, font, TEXT, frame)

    def _button_at(self, position: tuple[int, int]) -> str | None:
        if self.wall_button.collidepoint(position):
            return "wall"
        if self.restart_button.collidepoint(position):
            return "restart"
        if self.help_button.collidepoint(position):
            return "help"
        return None

    def _button_is_pressed(self, name: str) -> bool:
        return (
            self.button_pressed == name
            and pygame.time.get_ticks() < self.button_pressed_until
        )

    @staticmethod
    def _garden_tile_for_cell(x: int, y: int) -> tuple[int, int]:
        right = BOARD_SIZE - 1
        bottom = BOARD_SIZE - 1
        if y == 0:
            if x == 0:
                return GARDEN_GRASS_TOP_LEFT
            if x == right:
                return GARDEN_GRASS_TOP_RIGHT
            return GARDEN_GRASS_TOP
        if y == bottom:
            if x == 0:
                return GARDEN_GRASS_BOTTOM_LEFT
            if x == right:
                return GARDEN_GRASS_BOTTOM_RIGHT
            return GARDEN_GRASS_BOTTOM
        if x == 0:
            return GARDEN_GRASS_LEFT
        if x == right:
            return GARDEN_GRASS_RIGHT
        return GARDEN_GRASS_CENTER

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
        raise ValueError(
            f"Pawn move must be one orthogonal square or straight jump, got {delta}."
        )

    @staticmethod
    def _text(
        screen: pygame.Surface,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        position: tuple[int, int],
    ) -> None:
        screen.blit(font.render(text, True, color), position)

    @staticmethod
    def _fitted_text(
        screen: pygame.Surface,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        position: tuple[int, int],
        max_width: int,
    ) -> None:
        image = font.render(text, True, color)
        if image.get_width() > max_width:
            height = max(1, round(image.get_height() * max_width / image.get_width()))
            image = pygame.transform.scale(image, (max_width, height))
        screen.blit(image, position)

    @staticmethod
    def _center_text(
        screen: pygame.Surface,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        rect: pygame.Rect,
    ) -> None:
        image = font.render(text, True, color)
        screen.blit(image, image.get_rect(center=rect.center))

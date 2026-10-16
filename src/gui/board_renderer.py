"""Board geometry and drawing for the Pygame interface."""

from __future__ import annotations

import pygame

from src.engine.board import BOARD_SIZE, Board, Move, Orientation
from src.gui.assets import GameAssets
from src.gui.theme import (
    GARDEN_BACKGROUND_TILE_SIZE,
    GARDEN_DIRT,
    GARDEN_GRASS_BOTTOM,
    GARDEN_GRASS_BOTTOM_LEFT,
    GARDEN_GRASS_BOTTOM_RIGHT,
    GARDEN_GRASS_CENTER,
    GARDEN_GRASS_LEFT,
    GARDEN_GRASS_RIGHT,
    GARDEN_GRASS_TOP,
    GARDEN_GRASS_TOP_LEFT,
    GARDEN_GRASS_TOP_RIGHT,
    HIGHLIGHT,
    HIGHLIGHT_OUTLINE,
    PANEL_BORDER,
    PANEL_SHADOW,
    PAWN_MOVE_ANIMATION_MS,
    PAWN_SPRITE_CELL_SCALE,
    PLAYER_COLORS,
    SPRITE_COLUMNS,
    SPRITE_ROW_BY_DIRECTION,
    WALL_COLOR,
    Direction,
    Position,
)

MoveRecord = tuple[int, Move, Position | None]
PawnAnimation = tuple[Position, Position, int]


class BoardRenderer:
    """Render the board and own its responsive cell and wall geometry."""

    def __init__(self, assets: GameAssets) -> None:
        self.assets = assets
        self.board_rect = pygame.Rect(0, 0, 0, 0)
        self.gap = 0.0
        self.cell_size = 0.0
        self.stride = 0.0

    def set_layout(self, board_rect: pygame.Rect, gap: float) -> None:
        """Set board geometry for the current viewport."""
        self.board_rect = board_rect
        self.gap = gap
        self.cell_size = (board_rect.width - gap * (BOARD_SIZE - 1)) / BOARD_SIZE
        self.stride = self.cell_size + gap

    def draw(
        self,
        screen: pygame.Surface,
        board: Board,
        move_records: list[MoveRecord],
        wall_mode: bool,
        wall_orientation: Orientation,
        pawn_directions: list[Direction],
        pawn_animations: dict[int, PawnAnimation],
    ) -> None:
        """Draw the board background, tiles, walls, preview, and pawns."""
        corner_radius = max(8, round(self.cell_size * 0.22))
        pygame.draw.rect(
            screen,
            PANEL_SHADOW,
            self.board_rect,
            border_radius=corner_radius,
        )
        self._draw_rounded_tiled_texture(
            screen,
            self.assets.tile_surface(*GARDEN_DIRT, GARDEN_BACKGROUND_TILE_SIZE),
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
        self._draw_tiles(screen, board, move_records, wall_mode)
        self._draw_walls(screen, board, move_records)
        self._draw_wall_preview(screen, board, wall_mode, wall_orientation)
        self._draw_pawns(screen, board, pawn_directions, pawn_animations)

    def wall_anchor(self, position: tuple[int, int]) -> tuple[int, int]:
        """Convert a pointer position to a wall anchor."""
        offset = self.gap / 2
        x = round(
            (position[0] - self.board_rect.left - self.stride + offset)
            / self.stride
        )
        y = round(
            (position[1] - self.board_rect.top - self.stride + offset)
            / self.stride
        )
        return x, y

    def cell_rect(self, x: int, y: int) -> pygame.Rect:
        """Return the pixel bounds for a board cell."""
        return pygame.Rect(
            round(self.board_rect.left + x * self.stride),
            round(self.board_rect.top + y * self.stride),
            round(self.cell_size),
            round(self.cell_size),
        )

    def wall_rect(self, x: int, y: int, orientation: Orientation) -> pygame.Rect:
        """Return the pixel bounds for a wall anchor and orientation."""
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

    def _draw_tiles(
        self,
        screen: pygame.Surface,
        board: Board,
        move_records: list[MoveRecord],
        wall_mode: bool,
    ) -> None:
        legal_destinations = {
            (move.x, move.y) for move in board.get_legal_pawn_moves()
        }
        last_entry = move_records[-1] if move_records else None
        pulse = (pygame.time.get_ticks() % 1200) / 1200
        pulse_scale = 0.9 + 0.1 * (1 - abs(2 * pulse - 1))
        for y in range(BOARD_SIZE):
            for x in range(BOARD_SIZE):
                rect = self.cell_rect(x, y)
                tile_x, tile_y = self._garden_tile_for_cell(x, y)
                screen.blit(self.assets.tile_surface(tile_x, tile_y, rect.width), rect)
                goal_player = 0 if y == 0 else 1 if y == BOARD_SIZE - 1 else None
                if goal_player is not None and x == 0:
                    self._draw_goal_house(screen, rect, goal_player)
                if (
                    last_entry is not None
                    and last_entry[1].kind == "pawn"
                    and last_entry[2] == (x, y)
                ):
                    self._draw_last_move_cell(screen, rect, last_entry[0])
                if (x, y) in legal_destinations and not wall_mode:
                    radius = max(4, round(self.cell_size * 0.105 * pulse_scale))
                    dot_size = radius * 2 + 4
                    dot = pygame.Surface((dot_size, dot_size), pygame.SRCALPHA)
                    dot_center = (dot_size // 2, dot_size // 2)
                    pygame.draw.circle(
                        dot,
                        (*HIGHLIGHT_OUTLINE, 115),
                        dot_center,
                        radius + 2,
                    )
                    pygame.draw.circle(
                        dot,
                        (*HIGHLIGHT, 155),
                        dot_center,
                        radius,
                    )
                    screen.blit(dot, dot.get_rect(center=rect.center))

    @staticmethod
    def _draw_last_move_cell(
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
        house = pygame.transform.scale(self.assets.goal_house_sprites[player], (size, size))
        screen.blit(house, house.get_rect(center=rect.center))

    def _draw_walls(
        self,
        screen: pygame.Surface,
        board: Board,
        move_records: list[MoveRecord],
    ) -> None:
        for orientation, x, y in board.walls:
            rect = self.wall_rect(x, y, orientation)
            pygame.draw.rect(screen, (65, 45, 34), rect.move(1, 3), border_radius=5)
            pygame.draw.rect(screen, WALL_COLOR, rect, border_radius=5)
            shine = rect.inflate(
                -max(3, int(self.gap * 0.45)),
                -max(3, int(self.gap * 0.45)),
            )
            if shine.width > 0 and shine.height > 0:
                pygame.draw.rect(screen, (133, 95, 65), shine, border_radius=3)
            if move_records and move_records[-1][1] == Move.wall(x, y, orientation):
                pygame.draw.rect(
                    screen,
                    HIGHLIGHT,
                    rect.inflate(4, 4),
                    width=max(2, round(self.gap)),
                )

    def _draw_wall_preview(
        self,
        screen: pygame.Surface,
        board: Board,
        wall_mode: bool,
        wall_orientation: Orientation,
    ) -> None:
        if not wall_mode or board.is_game_over():
            return
        mouse_position = pygame.mouse.get_pos()
        if not self.board_rect.collidepoint(mouse_position):
            return
        x, y = self.wall_anchor(mouse_position)
        move = Move.wall(x, y, wall_orientation)
        color = (
            PLAYER_COLORS[board.current_player]
            if board.is_legal_move(move)
            else (210, 70, 66)
        )
        rect = self.wall_rect(x, y, wall_orientation)
        preview = pygame.Surface(rect.size, pygame.SRCALPHA)
        preview.fill((*color, 145))
        screen.blit(preview, rect)
        pygame.draw.rect(screen, (*color, 235), rect, width=max(2, round(self.gap)))

    def _draw_pawns(
        self,
        screen: pygame.Surface,
        board: Board,
        pawn_directions: list[Direction],
        pawn_animations: dict[int, PawnAnimation],
    ) -> None:
        now = pygame.time.get_ticks()
        for player, position in enumerate(board.pawns):
            center = self.cell_rect(*position).center
            animation = pawn_animations.get(player)
            frame_index = 0
            if animation is not None:
                start, destination, started_at = animation
                elapsed = now - started_at
                if destination == position and elapsed < PAWN_MOVE_ANIMATION_MS:
                    progress = max(0.0, elapsed / PAWN_MOVE_ANIMATION_MS)
                    start_center = self.cell_rect(*start).center
                    end_center = self.cell_rect(*destination).center
                    center = (
                        round(start_center[0] + (end_center[0] - start_center[0]) * progress),
                        round(start_center[1] + (end_center[1] - start_center[1]) * progress),
                    )
                    frame_index = min(
                        SPRITE_COLUMNS - 1,
                        int(progress * SPRITE_COLUMNS),
                    )

            direction_row = SPRITE_ROW_BY_DIRECTION[pawn_directions[player]]
            frame = self.assets.bunny_frames[direction_row][frame_index]
            frame_size = max(1, round(self.cell_size * PAWN_SPRITE_CELL_SCALE))
            scaled_frame = pygame.transform.scale(frame, (frame_size, frame_size))
            screen.blit(scaled_frame, scaled_frame.get_rect(center=center))

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

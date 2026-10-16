"""Load and cache pixel-art assets used by the game UI."""

from pathlib import Path

import pygame

from src.gui.theme import (
    GOAL_HOUSE_SPRITE_RECTS,
    SPRITE_COLUMNS,
    SPRITE_ROWS,
    SPRITE_SIZE,
    TILESET_TILE_SIZE,
    PLAYER_COLORS,
)


class GameAssets:
    """Own the loaded sprite sheets, fonts, and scaled tile cache."""

    def __init__(self, asset_root: Path) -> None:
        font_dir = asset_root / "Tileset" / "fonts"
        self.pixel_font = pygame.font.Font(str(font_dir / "PixelifySans-Regular.ttf"), 18)
        self.pixel_bold_font = pygame.font.Font(str(font_dir / "PixelifySans-Bold.ttf"), 24)
        self.pixel_small_font = pygame.font.Font(str(font_dir / "PixelifySans-Regular.ttf"), 14)

        sprite_sheet = pygame.image.load(str(asset_root / "Bunny_Run.png"))
        expected_size = (SPRITE_SIZE * SPRITE_COLUMNS, SPRITE_SIZE * SPRITE_ROWS)
        if sprite_sheet.get_size() != expected_size:
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

        self.tileset = pygame.image.load(
            str(asset_root / "Tileset" / "Autotile_Grass_and_Dirt_Path_Tileset.png")
        )
        house_tileset = pygame.image.load(str(asset_root / "Tileset" / "House_Tileset.png"))
        self.goal_house_sprites = [
            self.recolor_goal_house(house_tileset.subsurface(rect), player)
            for player, rect in enumerate(GOAL_HOUSE_SPRITE_RECTS)
        ]
        self._scaled_tiles: dict[tuple[int, int, int], pygame.Surface] = {}

    def tile_surface(self, tile_x: int, tile_y: int, size: int) -> pygame.Surface:
        """Return a nearest-neighbor-scaled atlas tile, cached by tile and size."""
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
    def recolor_goal_house(source: pygame.Surface, player: int) -> pygame.Surface:
        """Apply a player's UI color to the roof pixels of a house sprite."""
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
                recolored = tuple(
                    min(255, round(channel * scale))
                    for channel in target
                )
                sprite.set_at((x, y), (*recolored, alpha))
        return sprite

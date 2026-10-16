"""Sidebar layout and pixel-art controls for the Pygame interface."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from src.engine.board import Board, Orientation
from src.gui.assets import GameAssets
from src.gui.theme import (
    MUTED,
    PANEL,
    PANEL_BORDER,
    PANEL_INSET,
    PANEL_SHADOW,
    PLAYER_CARD_FILL,
    PLAYER_CARD_INACTIVE,
    PLAYER_CARD_MUTED,
    PLAYER_COLORS,
    TEXT,
    SPRITE_ROW_BY_DIRECTION,
)


@dataclass
class SidebarState:
    """Mutable interface state needed to draw the sidebar."""

    board: Board
    wall_mode: bool
    wall_orientation: Orientation
    help_visible: bool
    player_times_ms: list[int]
    button_pressed: str | None
    button_pressed_until: int


class SidebarRenderer:
    """Draw player cards, controls, and responsive help content."""

    def __init__(self, assets: GameAssets) -> None:
        self.assets = assets

    def draw(
        self,
        screen: pygame.Surface,
        panel: pygame.Rect,
        compact: bool,
        state: SidebarState,
    ) -> tuple[pygame.Rect, pygame.Rect, pygame.Rect]:
        """Render the sidebar and return wall, restart, and help hitboxes."""
        pygame.draw.rect(screen, PANEL_SHADOW, panel.move(4, 4))
        pygame.draw.rect(screen, PANEL_BORDER, panel)
        inner = panel.inflate(-6, -6)
        pygame.draw.rect(screen, PANEL, inner)
        pygame.draw.rect(screen, PANEL_INSET, inner.inflate(-6, -6), width=1)

        left = inner.x + 14
        right = inner.right - 14
        current = state.board.current_player
        winner = state.board.winner
        turn_text = (
            f"PLAYER {winner + 1} WINS!"
            if winner is not None
            else f"PLAYER {current + 1}'S TURN"
        )
        turn_player = winner if winner is not None else current
        if compact:
            return self._draw_compact_panel(
                screen,
                inner,
                left,
                right,
                turn_text,
                turn_player,
                state,
            )
        return self._draw_full_panel(
            screen,
            inner,
            left,
            right,
            winner,
            state,
        )

    def _draw_full_panel(
        self,
        screen: pygame.Surface,
        inner: pygame.Rect,
        left: int,
        right: int,
        winner: int | None,
        state: SidebarState,
    ) -> tuple[pygame.Rect, pygame.Rect, pygame.Rect]:
        self._text(screen, "BUNNY HOLLOW", self.assets.pixel_bold_font, TEXT, (left, inner.y + 10))
        self._text(
            screen,
            "GARDEN QUORIDOR",
            self.assets.pixel_small_font,
            MUTED,
            (left + 1, inner.y + 39),
        )
        pygame.draw.line(screen, PANEL_INSET, (left, inner.y + 61), (right, inner.y + 61), 2)
        if winner is not None:
            self._text(
                screen,
                f"PLAYER {winner + 1} WINS!",
                self.assets.pixel_small_font,
                PLAYER_COLORS[winner],
                (left, inner.y + 66),
            )
        self._draw_player_cards(
            screen,
            left,
            right,
            inner.y + 82,
            84,
            state,
            compact=False,
        )
        button_width = right - left
        wall_button = pygame.Rect(left, inner.y + 178, button_width, 36)
        restart_button = pygame.Rect(left, inner.y + 223, button_width, 34)
        help_button = pygame.Rect(left, inner.y + 266, button_width, 32)
        self._draw_wall_mode_toggle(screen, wall_button, state)
        self._draw_button(
            screen,
            restart_button,
            "NEW GAME  [N]",
            state,
            pressed=self._button_is_pressed(state, "restart"),
        )
        self._draw_button(
            screen,
            help_button,
            "HELP  [H]",
            state,
            active=state.help_visible,
            pressed=self._button_is_pressed(state, "help"),
        )
        if state.help_visible:
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
                    self.assets.pixel_small_font,
                    TEXT,
                    (left, inner.y + 310 + index * 16),
                    right - left,
                )
        else:
            self._fitted_text(
                screen,
                "DOT: MOVE  H: HELP",
                self.assets.pixel_small_font,
                MUTED,
                (left, inner.bottom - 25),
                right - left,
            )
        return wall_button, restart_button, help_button

    def _draw_compact_panel(
        self,
        screen: pygame.Surface,
        inner: pygame.Rect,
        left: int,
        right: int,
        turn_text: str,
        turn_player: int,
        state: SidebarState,
    ) -> tuple[pygame.Rect, pygame.Rect, pygame.Rect]:
        self._text(screen, "BUNNY HOLLOW", self.assets.pixel_font, TEXT, (left, inner.y + 3))
        if "WINS" in turn_text:
            self._text(
                screen,
                f"P{turn_player + 1} WINS!",
                self.assets.pixel_small_font,
                PLAYER_COLORS[turn_player],
                (left, inner.y + 23),
            )
        self._draw_player_cards(
            screen,
            left,
            right,
            inner.y + 27,
            61,
            state,
            compact=True,
        )

        button_gap = 5
        button_y = inner.y + 92
        button_height = 25
        button_width = max(44, (right - left - button_gap * 2) // 3)
        wall_button = pygame.Rect(left, button_y, button_width, button_height)
        restart_button = pygame.Rect(
            wall_button.right + button_gap,
            button_y,
            button_width,
            button_height,
        )
        help_button = pygame.Rect(
            restart_button.right + button_gap,
            button_y,
            right - restart_button.right - button_gap,
            button_height,
        )
        self._draw_wall_mode_toggle(screen, wall_button, state, compact=True)
        self._draw_button(
            screen,
            restart_button,
            "NEW",
            state,
            pressed=self._button_is_pressed(state, "restart"),
            compact=True,
        )
        self._draw_button(
            screen,
            help_button,
            "HELP",
            state,
            active=state.help_visible,
            pressed=self._button_is_pressed(state, "help"),
            compact=True,
        )
        if inner.height >= 185:
            help_top = button_y + button_height + 9
            if state.help_visible:
                self._draw_compact_help(
                    screen,
                    pygame.Rect(left, help_top, right - left, inner.bottom - help_top - 22),
                )
            else:
                self._fitted_text(
                    screen,
                    "W: WALL MODE  R: ROTATE  BACKSPACE: UNDO",
                    self.assets.pixel_small_font,
                    MUTED,
                    (left, help_top),
                    right - left,
                )
        elif inner.height >= 125:
            hint = "W WALL  R ROTATE  N NEW  H CLOSE" if state.help_visible else (
                "WALL: R ROTATES  |  H: HELP"
                if state.wall_mode
                else "DOT: MOVE  H: HELP"
            )
            self._fitted_text(
                screen,
                hint,
                self.assets.pixel_small_font,
                MUTED,
                (left, inner.bottom - 18),
                right - left,
            )
        return wall_button, restart_button, help_button

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
                self.assets.pixel_small_font,
                TEXT,
                (rect.x + 6, rect.y + 5 + index * 16),
                rect.width - 12,
            )

    def _draw_wall_mode_toggle(
        self,
        screen: pygame.Surface,
        rect: pygame.Rect,
        state: SidebarState,
        *,
        compact: bool = False,
    ) -> None:
        active = state.wall_mode
        selected_color = PLAYER_COLORS[state.board.current_player]
        face = (
            tuple((channel + 255) // 2 for channel in selected_color)
            if active
            else (232, 209, 170)
        )
        frame = rect.move(0, 2) if self._button_is_pressed(state, "wall") else rect
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
        font = self.assets.pixel_small_font if compact else self.assets.pixel_font
        label_image = font.render(label, True, TEXT)
        screen.blit(label_image, label_image.get_rect(midleft=(frame.left + 7, frame.centery)))

        icon_width = 14 if compact else 20
        icon_height = 5 if compact else 6
        icon_center_x = frame.right - (14 if compact else 22)
        icon_center_y = frame.centery
        if state.wall_orientation == "horizontal":
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
        state: SidebarState,
        *,
        compact: bool = False,
    ) -> None:
        gap = 6
        card_width = (right - left - gap) // 2
        active_player = (
            state.board.winner
            if state.board.winner is not None
            else state.board.current_player
        )
        for player in (0, 1):
            card = pygame.Rect(left + player * (card_width + gap), y, card_width, height)
            active = player == active_player
            fill = PLAYER_CARD_FILL if active else PLAYER_CARD_INACTIVE
            border_width = 4 if active else 1
            glow_color = tuple(min(255, channel + 38) for channel in PLAYER_COLORS[player])
            if active:
                pygame.draw.rect(screen, glow_color, card.inflate(4, 4), width=2)
            pygame.draw.rect(screen, PLAYER_COLORS[player], card, width=border_width)
            pygame.draw.rect(screen, fill, card.inflate(-border_width * 2, -border_width * 2))

            portrait_size = 24 if compact else 40
            portrait_source = self.assets.bunny_frames[
                SPRITE_ROW_BY_DIRECTION["down" if player == 0 else "up"]
            ][0]
            portrait_source = portrait_source.subsurface(portrait_source.get_bounding_rect())
            portrait = pygame.transform.scale(portrait_source, (portrait_size, portrait_size))
            portrait_rect = pygame.Rect(card.x + 5, card.y + 4, portrait_size, portrait_size)
            screen.blit(portrait, portrait_rect)

            text_x = portrait_rect.right + 5
            text_color = TEXT if active else PLAYER_CARD_MUTED
            self._text(
                screen,
                f"P{player + 1}",
                self.assets.pixel_small_font,
                text_color,
                (text_x, card.y + 2),
            )
            remaining = state.board.walls_remaining[player]
            self._text(
                screen,
                f"{remaining}/10",
                self.assets.pixel_small_font,
                text_color,
                (text_x, card.y + (18 if compact else 21)),
            )
            timer_y = card.y + (33 if compact else 40)
            timer_color = PLAYER_COLORS[player] if active else PLAYER_CARD_MUTED
            self._draw_clock_icon(screen, text_x + 4, timer_y + 7, timer_color)
            self._text(
                screen,
                self._format_time(state.player_times_ms[player]),
                self.assets.pixel_small_font,
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
                    slot_color = PLAYER_COLORS[player] if active else tuple(
                        (channel + muted_channel * 2) // 3
                        for channel, muted_channel in zip(
                            PLAYER_COLORS[player],
                            PLAYER_CARD_MUTED,
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

    def _draw_button(
        self,
        screen: pygame.Surface,
        rect: pygame.Rect,
        label: str,
        state: SidebarState,
        *,
        active: bool = False,
        pressed: bool = False,
        compact: bool = False,
    ) -> None:
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        down = pressed and hovered
        selected_color = PLAYER_COLORS[state.board.current_player]
        face = (
            tuple((channel + 255) // 2 for channel in selected_color)
            if active
            else (255, 245, 218) if hovered else (232, 209, 170)
        )
        frame = rect.move(0, 2) if down else rect
        pygame.draw.rect(screen, PANEL_SHADOW, rect.move(0, 3))
        pygame.draw.rect(screen, PANEL_BORDER, frame)
        pygame.draw.rect(screen, face, frame.inflate(-4, -4))
        if active:
            pygame.draw.rect(screen, selected_color, frame.inflate(-2, -2), width=2)
        font = self.assets.pixel_small_font if compact else self.assets.pixel_font
        self._center_text(screen, label, font, TEXT, frame)

    @staticmethod
    def _button_is_pressed(state: SidebarState, name: str) -> bool:
        return (
            state.button_pressed == name
            and pygame.time.get_ticks() < state.button_pressed_until
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

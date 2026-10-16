"""Pygame interface for the first playable Quoridor milestone."""

from __future__ import annotations

import pygame

from src.engine.board import BOARD_SIZE, Board, Move, Orientation

BACKGROUND = (242, 236, 218)
PANEL = (255, 250, 238)
TEXT = (57, 65, 53)
MUTED = (119, 125, 108)
BOARD_DARK = (133, 96, 64)
TILE = (224, 195, 145)
TILE_ALT = (232, 207, 163)
GRID = (174, 134, 91)
WALL_COLOR = (94, 62, 43)
PLAYER_COLORS = ((219, 102, 123), (65, 156, 153))
HIGHLIGHT = (133, 176, 106)


class QuoridorGame:
    """Draw the board and handle local two-player input."""

    def __init__(self) -> None:
        self.board = Board()
        self.wall_mode = False
        self.wall_orientation: Orientation = "horizontal"
        self.message = "Choose a highlighted square to move."
        self.window_size = (1100, 800)
        self.fullscreen = False
        self.font = pygame.font.Font(None, 27)
        self.small_font = pygame.font.Font(None, 21)
        self.title_font = pygame.font.Font(None, 44)
        self.board_rect = pygame.Rect(0, 0, 0, 0)
        self.cell_size = 0.0
        self.gap = 0.0
        self.stride = 0.0
        self.wall_button = pygame.Rect(0, 0, 0, 0)
        self.restart_button = pygame.Rect(0, 0, 0, 0)

    def run(self) -> None:
        """Run the resizable 60 FPS game window."""
        screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
        pygame.display.set_caption("Bunny Hollow | Quoridor")
        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE and not self.fullscreen:
                    self.window_size = event.size
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
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
                    elif event.key == pygame.K_r:
                        self.wall_orientation = (
                            "vertical" if self.wall_orientation == "horizontal" else "horizontal"
                        )
                    elif event.key == pygame.K_BACKSPACE and self.board.last_move is not None:
                        last_move = self.board.last_move
                        self.board.undo_move(last_move)
                        self.message = "Last move undone."
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_click(event.pos)

            screen.fill(BACKGROUND)
            self._draw(screen)
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

    def _draw(self, screen: pygame.Surface) -> None:
        width, height = screen.get_size()
        gap = max(5, min(11, height * 0.014))
        board_size = min(height - 150, width - 390, 650)
        board_size = max(360, board_size)
        board_x = max(24, (width - board_size - 350) // 2)
        board_y = (height - board_size) // 2
        self.board_rect = pygame.Rect(board_x, board_y, board_size, board_size)
        self.gap = gap
        self.cell_size = (board_size - gap * (BOARD_SIZE - 1)) / BOARD_SIZE
        self.stride = self.cell_size + gap

        shadow = self.board_rect.move(0, 7)
        pygame.draw.rect(screen, (201, 187, 158), shadow, border_radius=20)
        pygame.draw.rect(screen, BOARD_DARK, self.board_rect, border_radius=20)
        self._draw_tiles(screen)
        self._draw_walls(screen)
        self._draw_pawns(screen)
        self._draw_panel(screen, board_x + board_size + 28, width, height)

    def _draw_tiles(self, screen: pygame.Surface) -> None:
        legal_destinations = {
            (move.x, move.y) for move in self.board.get_legal_pawn_moves()
        }
        current_pawn = self.board.pawns[self.board.current_player]
        for y in range(BOARD_SIZE):
            for x in range(BOARD_SIZE):
                rect = self._cell_rect(x, y)
                color = TILE_ALT if (x + y) % 2 else TILE
                pygame.draw.rect(screen, color, rect, border_radius=7)
                pygame.draw.rect(screen, GRID, rect, width=1, border_radius=7)
                if (x, y) in legal_destinations and not self.wall_mode:
                    pygame.draw.circle(screen, HIGHLIGHT, rect.center, max(5, int(self.gap * 0.72)))
                if (x, y) == current_pawn:
                    pygame.draw.rect(
                        screen,
                        (255, 241, 199),
                        rect.inflate(-4, -4),
                        width=3,
                        border_radius=7,
                    )

    def _draw_walls(self, screen: pygame.Surface) -> None:
        for orientation, x, y in self.board.walls:
            rect = self._wall_rect(x, y, orientation)
            pygame.draw.rect(screen, (65, 45, 34), rect.move(1, 3), border_radius=5)
            pygame.draw.rect(screen, WALL_COLOR, rect, border_radius=5)
            shine = rect.inflate(-max(3, int(self.gap * 0.45)), -max(3, int(self.gap * 0.45)))
            if shine.width > 0 and shine.height > 0:
                pygame.draw.rect(screen, (133, 95, 65), shine, border_radius=3)

    def _draw_pawns(self, screen: pygame.Surface) -> None:
        for player, position in enumerate(self.board.pawns):
            center = self._cell_rect(*position).center
            radius = max(12, int(self.cell_size * 0.32))
            color = PLAYER_COLORS[player]
            pygame.draw.ellipse(
                screen,
                color,
                (center[0] - radius * 0.65, center[1] - radius * 1.45, radius * 0.53, radius * 1.2),
            )
            pygame.draw.ellipse(
                screen,
                color,
                (center[0] + radius * 0.12, center[1] - radius * 1.45, radius * 0.53, radius * 1.2),
            )
            pygame.draw.circle(screen, (70, 55, 50), center, radius + 2)
            pygame.draw.circle(screen, color, center, radius)
            pygame.draw.circle(screen, (255, 255, 244), (center[0] - radius // 3, center[1] - radius // 7), max(2, radius // 9))
            pygame.draw.circle(screen, (255, 255, 244), (center[0] + radius // 3, center[1] - radius // 7), max(2, radius // 9))

    def _draw_panel(
        self,
        screen: pygame.Surface,
        panel_x: int,
        width: int,
        height: int,
    ) -> None:
        panel_width = width - panel_x - 24
        if panel_width < 240:
            panel_x = max(16, width - max(250, panel_width) - 20)
            panel_width = width - panel_x - 20
        panel = pygame.Rect(panel_x, 34, panel_width, height - 68)
        pygame.draw.rect(screen, PANEL, panel, border_radius=20)

        self._text(screen, "Bunny Hollow", self.title_font, TEXT, (panel.x + 22, panel.y + 24))
        self._text(screen, "QUORIDOR", self.small_font, MUTED, (panel.x + 24, panel.y + 68))

        current = self.board.current_player
        if self.board.winner is None:
            turn_text = f"Player {current + 1}'s turn"
            turn_color = PLAYER_COLORS[current]
        else:
            turn_text = f"Player {self.board.winner + 1} wins!"
            turn_color = PLAYER_COLORS[self.board.winner]
        pygame.draw.circle(screen, turn_color, (panel.x + 32, panel.y + 120), 11)
        self._text(screen, turn_text, self.font, TEXT, (panel.x + 54, panel.y + 107))

        for player in (0, 1):
            y = panel.y + 158 + player * 46
            pygame.draw.circle(screen, PLAYER_COLORS[player], (panel.x + 32, y + 10), 9)
            label = f"Player {player + 1}   |   {self.board.walls_remaining[player]} walls"
            self._text(screen, label, self.small_font, MUTED, (panel.x + 52, y))

        self.wall_button = pygame.Rect(panel.x + 20, panel.y + 272, panel.width - 40, 48)
        button_color = (217, 231, 198) if self.wall_mode else (235, 224, 200)
        pygame.draw.rect(screen, button_color, self.wall_button, border_radius=12)
        wall_label = (
            f"Wall: {self.wall_orientation.title()} (W)"
            if self.wall_mode
            else "Place a wall (W)"
        )
        self._center_text(screen, wall_label, self.font, TEXT, self.wall_button)

        self.restart_button = pygame.Rect(panel.x + 20, panel.y + 332, panel.width - 40, 44)
        pygame.draw.rect(screen, (232, 226, 211), self.restart_button, border_radius=12)
        self._center_text(screen, "New game (N)", self.small_font, TEXT, self.restart_button)

        info_y = panel.y + 406
        self._text(screen, "HOW TO PLAY", self.small_font, MUTED, (panel.x + 22, info_y))
        instructions = (
            "Click a highlighted tile to move.",
            "W: wall mode   R: rotate wall",
            "Click the board to place a wall.",
            "Backspace: undo   F11: fullscreen",
            "Esc: quit",
        )
        for index, line in enumerate(instructions):
            self._text(
                screen,
                line,
                self.small_font,
                TEXT,
                (panel.x + 22, info_y + 32 + index * 27),
            )
        pygame.draw.line(
            screen,
            (224, 215, 195),
            (panel.x + 20, panel.bottom - 95),
            (panel.right - 20, panel.bottom - 95),
            1,
        )
        self._text(
            screen,
            self.message,
            self.small_font,
            MUTED,
            (panel.x + 22, panel.bottom - 78),
        )

    def _handle_click(self, position: tuple[int, int]) -> None:
        if self.restart_button.collidepoint(position):
            self._restart()
            return
        if self.wall_button.collidepoint(position):
            self.wall_mode = not self.wall_mode
            self.message = "Click a wall slot to place it." if self.wall_mode else "Choose a highlighted square to move."
            return
        if not self.board_rect.collidepoint(position) or self.board.is_game_over():
            return

        if self.wall_mode:
            x, y = self._wall_anchor(position)
            move = Move.wall(x, y, self.wall_orientation)
            if self.board.is_legal_move(move):
                self.board.make_move(move)
                self.wall_mode = False
                self.message = "Wall placed. Your opponent's turn."
            else:
                self.message = "That wall placement is not legal."
            return

        for move in self.board.get_legal_pawn_moves():
            if self._cell_rect(move.x, move.y).collidepoint(position):
                self.board.make_move(move)
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

    def _restart(self) -> None:
        self.board = Board()
        self.wall_mode = False
        self.wall_orientation = "horizontal"
        self.message = "Choose a highlighted square to move."

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
    def _center_text(
        screen: pygame.Surface,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        rect: pygame.Rect,
    ) -> None:
        image = font.render(text, True, color)
        screen.blit(image, image.get_rect(center=rect.center))

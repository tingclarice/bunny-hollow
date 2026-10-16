"""Application entry point for Bunny Hollow Quoridor."""

import pygame

from src.gui.game import QuoridorGame


def main() -> None:
    """Initialize Pygame and start a local two-player game."""
    pygame.init()
    QuoridorGame().run()


if __name__ == "__main__":
    main()

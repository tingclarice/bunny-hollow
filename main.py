"""Application entry point for the Quoridor game."""

import pygame


def main() -> None:
    """Initialize Pygame and run the application's main loop."""
    pygame.init()
    window_size = (1000, 800)
    screen = pygame.display.set_mode(window_size, pygame.RESIZABLE)
    pygame.display.set_caption("Quoridor")
    clock = pygame.time.Clock()
    running = True
    fullscreen = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE and not fullscreen:
                window_size = event.size
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode(
                            window_size,
                            pygame.RESIZABLE,
                        )

        # Rendering and game updates will be added in later development.
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()

import pygame

from src.shared import Shared
from src.state_enums import State
from src.terminal import Terminal
from src.utils import render_at


def scale_background_image(
    image: pygame.Surface, screen_size: tuple[int, int]
) -> pygame.Surface:
    """Scales the given image to stay in the same ratio
    and always be bigger than the screen size"""

    width, height = screen_size
    iwidth, iheight = image.get_size()

    ratio = max(width / iwidth, height / iheight)
    new_size = (int(iwidth * ratio), int(iheight * ratio))
    scaled_image = pygame.transform.smoothscale(image, new_size)

    return scaled_image


class GameState:
    def __init__(self) -> None:
        self.shared = Shared()
        self.next_state: State | None = None
        self.terminal = Terminal()
        if self.shared.data.image_file is not None:
            self.original_image = pygame.image.load(
                self.shared.data.image_file
            ).convert()
            self.image = scale_background_image(
                self.original_image, self.shared.screen.get_size()
            )
        else:
            self.image = None

    def update(self):
        self.terminal.update()
        for event in self.shared.events:
            if event.type == pygame.VIDEORESIZE and self.image is not None:
                self.image = scale_background_image(
                    self.original_image, self.shared.screen.get_size()
                )

    def draw(self):
        if self.image is not None:
            render_at(self.shared.screen, self.image, "center")
        self.terminal.draw()

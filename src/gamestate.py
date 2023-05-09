import pygame

from src.shared import Shared
from src.state_enums import State
from src.terminal import Terminal
from src.utils import render_at, scale_image_perfect


class GameState:
    def __init__(self) -> None:
        self.shared = Shared()
        self.next_state: State | None = None
        self.terminal = Terminal()
        if self.shared.data.image_file is not None:
            self.original_image = pygame.image.load(
                self.shared.data.image_file
            ).convert()
            self.image = scale_image_perfect(
                self.original_image, self.shared.screen.get_size()
            )
        else:
            self.image = None

    def on_ctrl_s(self):
        if self.shared.keys[pygame.K_LCTRL] and self.shared.keys[pygame.K_s]:
            self.next_state = State.SETTINGS

    def on_win_resize(self):
        for event in self.shared.events:
            if event.type == pygame.VIDEORESIZE and self.image is not None:
                self.image = scale_image_perfect(
                    self.original_image, self.shared.screen.get_size()
                )

    def update(self):
        self.terminal.update()
        self.on_win_resize()
        self.on_ctrl_s()

    def draw(self):
        if self.image is not None:
            render_at(self.shared.screen, self.image, "center")
        self.terminal.draw()

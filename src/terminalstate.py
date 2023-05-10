import pygame

from src.shared import Shared
from src.state_enums import State
from src.terminal import Terminal
from src.utils import render_at, scale_image_perfect


class TerminalState:
    def __init__(self) -> None:
        self.shared = Shared()
        self.next_state: State | None = None
        self.terminal = Terminal()

    def on_ctrl_s(self):
        if self.shared.keys[pygame.K_LCTRL] and self.shared.keys[pygame.K_s]:
            self.next_state = State.SETTINGS

    def update(self):
        self.terminal.update()
        self.on_ctrl_s()

    def draw(self):
        self.terminal.draw()

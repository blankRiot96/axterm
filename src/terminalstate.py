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

    def update(self):
        self.terminal.update()

    def draw(self):
        self.terminal.draw()

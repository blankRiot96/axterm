from src.state_enums import State
from src.terminal import Terminal


class GameState:
    def __init__(self) -> None:
        self.next_state: State | None = None
        self.terminal = Terminal()

    def update(self):
        self.terminal.update()

    def draw(self):
        self.terminal.draw()

from src.state_enums import State


class GameState:
    def __init__(self) -> None:
        self.next_state: State | None = None

    def update(self):
        ...

    def draw(self):
        ...

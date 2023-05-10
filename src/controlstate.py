from src.shared import Shared
from src.utils import get_font, render_at


class ControlState:
    FONT = get_font("assets/fonts/regular1.ttf", 24)

    def __init__(self) -> None:
        self.next_state = None
        self.shared = Shared()
        self.surface = self.FONT.render(
            """
CTRL + T -> Terminal
CTRL + S -> Settings
CTRL + Q -> Controls
            """,
            True,
            self.shared.data.theme["text-color"],
        )

    def update(self):
        ...

    def draw(self):
        render_at(self.shared.screen, self.surface, "center")

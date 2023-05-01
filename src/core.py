import asyncio

import pygame

from src.shared import Shared


class Core:
    BG_COLOR = "#282C34"

    def __init__(self) -> None:
        self.shared = Shared()
        self.win_init()
        from src.states import StateManager

        self.shared.dt = 0.0
        self.shared.mouse_pos = (0, 0)
        self.state_manager = StateManager()

    def win_init(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1024, 600), pygame.RESIZABLE)
        self.shared.screen = self.screen
        self.clock = pygame.time.Clock()
        pygame.display.set_caption("Terminal")
        pygame.display.set_icon(pygame.image.load("assets/images/logo.png"))

    def on_click(self):
        self.shared.clicked = False
        for event in self.shared.events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
                self.shared.clicked = True

    def update(self):
        self.shared.events = pygame.event.get()
        for event in self.shared.events:
            if event.type == pygame.QUIT:
                raise SystemExit

        self.on_click()
        self.shared.dt = self.clock.tick() / 1000
        self.shared.dt = min(self.shared.dt, 0.1)
        self.shared.mouse_pos = pygame.mouse.get_pos()
        self.shared.keys = pygame.key.get_pressed()

        self.state_manager.update()

        pygame.display.flip()

    def draw(self):
        self.screen.fill((self.BG_COLOR))
        self.state_manager.draw()

    async def run(self):
        while True:
            self.update()
            self.draw()
            await asyncio.sleep(0)


def main():
    game = Core()
    asyncio.run(game.run())

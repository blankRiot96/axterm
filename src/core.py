import asyncio
import os

import pygame
import pygame._sdl2

from src.data import DataManager
from src.shared import Shared


class Core:
    def __init__(self) -> None:
        self.shared = Shared()
        self.shared.data = DataManager()
        self.win_init()
        from src.states import StateManager

        self.shared.dt = 0.0
        self.shared.mouse_pos = (0, 0)
        self.state_manager = StateManager()

    def win_init(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1024, 600), pygame.RESIZABLE)

        self.shared.win = pygame._sdl2.Window.from_display_module()
        self.shared.win.opacity = self.shared.data.config["opacity"]

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
                self.shared.data.on_exit()
                raise SystemExit

        self.on_click()
        self.shared.dt = self.clock.tick() / 1000
        self.shared.dt = min(self.shared.dt, 0.1)
        self.shared.mouse_pos = pygame.mouse.get_pos()
        self.shared.mouse_press = pygame.mouse.get_pressed()
        self.shared.keys = pygame.key.get_pressed()

        self.state_manager.update()

        pygame.display.flip()

    def draw(self):
        self.screen.fill((self.shared.data.theme["background-color"]))
        self.state_manager.draw()

    async def run(self):
        while True:
            self.update()
            self.draw()
            await asyncio.sleep(0)


def main():
    os.system("cls || clear")
    game = Core()
    asyncio.run(game.run())

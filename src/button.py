import pygame
import pyperclip

from src.shared import Shared
from src.utils import Time, get_font, render_at


class CopyButton:
    TEXT = "Copy"
    SIZE = WIDTH, HEIGHT = 80, 25
    FONT = get_font("assets/fonts/bold1.ttf", 16)

    def __init__(self, output: str) -> None:
        self.shared = Shared()
        self.output = output
        self.hover_surf = pygame.Surface(self.SIZE)
        self.surf = pygame.Surface(self.SIZE)
        self.click_surf = pygame.Surface(self.SIZE)

        self.text_surf = self.FONT.render(self.TEXT, "True", "white")
        self.text_rect = self.text_surf.get_rect()

        # Colors
        self.hover_surf.fill("grey")
        self.surf.fill((100, 100, 100))
        self.click_surf.fill("green")

        self.image = self.surf
        self.hovering = False
        self.clicked = False
        self.rect = self.image.get_rect()
        self.click_timer = Time(0.15)
        self.color_click = False

    def on_hover(self):
        if not self.hovering and not self.color_click:
            self.image = self.surf
            return

        self.image = self.hover_surf

    def on_click(self):
        if self.click_timer.tick():
            self.color_click = False

        if self.color_click:
            self.image = self.click_surf
        if not self.clicked:
            return

        self.click_timer.reset()
        self.color_click = True
        pyperclip.copy(self.output.strip())

    def update(self):
        self.hovering = self.rect.collidepoint(self.shared.mouse_pos)
        self.clicked = self.shared.clicked and self.hovering

        self.on_hover()
        self.on_click()

    def draw(self, offset):
        self.image.set_alpha(150)
        self.rect.topleft = (300, offset + 32)
        self.text_rect.center = self.rect.center
        self.shared.screen.blit(self.image, self.rect)
        self.shared.screen.blit(self.text_surf, self.text_rect)

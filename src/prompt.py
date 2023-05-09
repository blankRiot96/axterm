import itertools
import re
import subprocess

import pygame

from src.data import exact_match
from src.shared import Shared
from src.utils import Time, get_font, render_at

SPECIAL_COMMANDS = ("exit", "cls", "clear", "cd")


class Prompt:
    FONT_1 = get_font("assets/fonts/bold1.ttf", 16)
    FONT_2 = get_font("assets/fonts/regular1.ttf", 16)

    def __init__(self) -> None:
        self.shared = Shared()
        self.full_surf = pygame.Surface(
            (self.shared.screen.get_width(), self.FONT_1.get_height()), pygame.SRCALPHA
        )
        self.released = False
        self.text = []
        self.blink_cursors = itertools.cycle(("|", ""))
        self.blinky_cursor = next(self.blink_cursors)
        self.timer = Time(0.5)
        self.del_timer = Time(0.1)
        self.start = False
        self.focused = True
        self.output_surf: None | pygame.Surface = None
        self.output: None | str = None
        self.executable = "pwsh"
        self.command = ""
        self.sim_surf: pygame.Surface | None = None
        self.suggestion: str | None = None
        self.form_surface()

    def remove_last_char(self):
        if not self.text:
            return
        self.text.pop()

    def get_input(self):
        for event in self.shared.events:
            if event.type == pygame.TEXTINPUT:
                self.blinky_cursor = "|"
                self.focused = True
                self.text.append(event.text)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.remove_last_char()
                    self.start = True
                    self.del_timer.reset()
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_BACKSPACE:
                    self.start = False

        if self.start:
            self.blinky_cursor = "|"
            if self.del_timer.tick():
                self.remove_last_char()
        self.command = "".join(self.text)

    def on_delete_line(self):
        if self.shared.keys[pygame.K_x] and self.shared.keys[pygame.K_LCTRL]:
            self.text.clear()

    def cleanse_output(self):
        self.output = re.sub(r"\x1b\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]", "", self.output)

    def gain_output(self):
        if self.command.strip() in SPECIAL_COMMANDS or "cd" in self.command:
            self.output = ""
            return
        try:
            self.output = subprocess.check_output(
                [self.executable, "-Command", self.command],
                shell=True,
                universal_newlines=True,
                cwd=self.shared.cwd,
            )
        except Exception as e:
            self.output = f"Command '{self.command}' returned non-zero exit status 1"

    def on_enter(self, event):
        if event.key != pygame.K_RETURN:
            return

        self.focused = False
        self.gain_output()
        self.cleanse_output()
        self.output_surf = self.FONT_2.render(
            self.output,
            True,
            self.shared.data.theme["output-color"],
        )
        self.full_surf = pygame.Surface(
            (
                Shared.SCREEN_WIDTH,
                self.FONT_1.get_height() + self.output_surf.get_height(),
            )
        )
        self.released = True
        self.form_surface()

    def on_fetch_command(self, key: int):
        if key == pygame.K_UP:
            self.shared.data.current_index -= 1
        else:
            self.shared.data.current_index += 1

        self.text = list(self.shared.data.current_line)

    def on_fetch_command_check(self, event):
        if event.key not in (pygame.K_DOWN, pygame.K_UP):
            return

        self.on_fetch_command(event.key)

    def blink_cursor(self):
        if not self.focused:
            self.blinky_cursor = ""
            return
        if self.timer.tick():
            self.blinky_cursor = next(self.blink_cursors)

    def form_surface(self):
        if self.released:
            self.blinky_cursor = ""
        self.surf = self.FONT_1.render(
            f"{self.shared.cwd.name}  {self.command}{self.blinky_cursor}",
            True,
            self.shared.data.theme["text-color"],
        )
        self.region = self.full_surf.get_rect(topleft=(10, 10))

        if self.suggestion is None or not self.command:
            self.sim_surf = None
            return
        self.sim_surf = self.FONT_1.render(
            f"{self.shared.cwd.name}  {self.suggestion}",
            True,
            self.shared.data.theme["suggestion-color"],
        )
        self.sim_surf.set_alpha(150)

    def regional_input(self):
        if not self.shared.clicked:
            return

        if self.region.inflate(self.shared.SCREEN_WIDTH, 0).collidepoint(
            self.shared.mouse_pos
        ):
            self.focused = True
        else:
            self.focused = False

    def get_suggestion(self):
        self.suggestion = exact_match(self.shared.data.command_history, self.command)
        if self.suggestion is None:
            return

    def on_autocomplete(self, event):
        if event.key in (pygame.K_TAB, pygame.K_RIGHT) and self.suggestion is not None:
            self.text = list(self.suggestion)

    def event_pool(self):
        for event in self.shared.events:
            if event.type == pygame.KEYDOWN:
                self.on_autocomplete(event)
                self.on_fetch_command_check(event)
                self.on_enter(event)

    def update(self):
        self.blink_cursor()
        self.get_input()
        self.get_suggestion()
        self.on_delete_line()
        self.regional_input()
        self.event_pool()

        self.form_surface()

    def draw(self, offset):
        self.full_surf = pygame.Surface(self.full_surf.get_size(), pygame.SRCALPHA)
        if self.sim_surf is not None:
            render_at(self.full_surf, self.sim_surf, "topleft")
        render_at(self.full_surf, self.surf, "topleft")
        if self.output_surf is not None:
            render_at(
                self.full_surf,
                self.output_surf,
                "topleft",
                (0, self.FONT_1.get_height()),
            )
        self.region.topleft = (10, 10 + offset)
        self.shared.screen.blit(self.full_surf, self.region.topleft)

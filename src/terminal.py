import itertools
import os
import re
import subprocess
import sys
from pathlib import Path

import pygame

from src.shared import Shared
from src.utils import Time, get_font, render_at


class Prompt:
    FONT_1 = get_font("assets/fonts/bold1.ttf", 16)
    FONT_2 = get_font("assets/fonts/regular1.ttf", 16)

    def __init__(self) -> None:
        self.shared = Shared()
        self.full_surf = pygame.Surface(
            (Shared.SCREEN_WIDTH, self.FONT_1.get_height()), pygame.SRCALPHA
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
        self.executable = "pwsh" if sys.platform == "win32" else None
        self.command = ""
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

    def on_delete_line(self):
        if self.shared.keys[pygame.K_x] and self.shared.keys[pygame.K_LCTRL]:
            self.text.clear()

    def cleanse_output(self):
        self.output = re.sub(r"\x1b\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]", "", self.output)

    def gain_output(self):
        command = "".join(self.text)
        try:
            if self.executable is None:
                self.output = subprocess.check_output(
                    command, shell=True, universal_newlines=True, cwd=self.shared.cwd
                )

                return
            self.output = subprocess.check_output(
                [self.executable, "-Command", command],
                shell=True,
                universal_newlines=True,
                cwd=self.shared.cwd,
            )
        except Exception as e:
            self.output = f"Command '{command}' returned non-zero exit status 1"

    def on_enter(self):
        for event in self.shared.events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.command = "".join(self.text)
                self.focused = False
                self.gain_output()
                self.cleanse_output()
                self.output_surf = self.FONT_2.render(
                    self.output,
                    True,
                    "white",
                )
                self.full_surf = pygame.Surface(
                    (
                        Shared.SCREEN_WIDTH,
                        self.FONT_1.get_height() + self.output_surf.get_height(),
                    )
                )
                self.released = True
                self.form_surface()

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
            f"{self.shared.cwd.name}  {''.join(self.text)}{self.blinky_cursor}",
            True,
            "white",
        )
        self.region = self.full_surf.get_rect(topleft=(10, 10))

    def regional_input(self):
        if not self.shared.clicked:
            return

        if self.region.inflate(self.shared.SCREEN_WIDTH, 0).collidepoint(
            self.shared.mouse_pos
        ):
            self.focused = True
        else:
            self.focused = False

    def update(self):
        self.blink_cursor()
        self.get_input()
        self.on_delete_line()
        self.regional_input()

        self.form_surface()

        self.on_enter()

    def draw(self, offset):
        self.full_surf = pygame.Surface(self.full_surf.get_size(), pygame.SRCALPHA)
        render_at(self.full_surf, self.surf, "topleft")
        if self.output_surf is not None:
            render_at(
                self.full_surf,
                self.output_surf,
                "topleft",
                (0, self.FONT_1.get_height()),
            )
        render_at(self.shared.screen, self.full_surf, "topleft", (10, 10 + offset))


class Terminal:
    def __init__(self) -> None:
        self.shared = Shared()
        self.shared.cwd = Path(os.path.expanduser("~"))

        self.prompts: list[Prompt] = [Prompt()]
        self.__current_prompt_index = 0
        self.current_prompt = self.prompts[self.__current_prompt_index]

    @property
    def current_prompt_index(self) -> int:
        return self.__current_prompt_index

    @current_prompt_index.setter
    def current_prompt_index(self, val: int) -> None:
        self.__current_prompt_index = val
        self.current_prompt = self.prompts[val]

    def update(self):
        self.current_prompt.update()
        if self.current_prompt.command == "cls":
            self.prompts.clear()
            self.prompts.append(Prompt())
            self.current_prompt_index = 0
        elif self.current_prompt.command == "exit":
            exit()
        elif "cd" in self.current_prompt.command:
            self.shared.cwd = subprocess.check_output(
                [
                    self.current_prompt.executable,
                    "-Command",
                    f"{self.current_prompt.command};py -c 'import os;print(os.getcwd())'",
                ],
                shell=True,
                universal_newlines=True,
                cwd=self.shared.cwd,
            )
            self.shared.cwd = Path(self.shared.cwd.replace("\\", "/"))

        if self.current_prompt.released:
            self.prompts.append(Prompt())
            self.current_prompt_index += 1

    def draw(self):
        offset = 0
        for prompt in self.prompts:
            prompt.draw(offset)
            offset += prompt.full_surf.get_height() + 10

import itertools
import os
import re
import subprocess
import time
from pathlib import Path

import pygame

from src.button import CopyButton
from src.shared import Shared
from src.utils import Time, get_font, render_at


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
        self.region.topleft = (10, 10 + offset)
        self.shared.screen.blit(self.full_surf, self.region.topleft)


class Terminal:
    SCROLL_SCALE = 15

    def __init__(self) -> None:
        self.shared = Shared()
        self.shared.cwd = Path(os.path.expanduser("~"))

        self.prompts: list[Prompt] = [Prompt()]
        self.__current_prompt_index = 0
        self.current_prompt = self.prompts[self.__current_prompt_index]
        self.copy_buttons = []

        self.perm_offset = 0
        self.start = None

    @property
    def current_prompt_index(self) -> int:
        return self.__current_prompt_index

    @current_prompt_index.setter
    def current_prompt_index(self, val: int) -> None:
        self.__current_prompt_index = val
        self.current_prompt = self.prompts[val]

    def change_directory(self):
        """Changes the directory in which the next prompt spawns"""

        command = f"{self.current_prompt.command};pwd"
        output = subprocess.check_output(
            [self.current_prompt.executable, "-Command", command],
            shell=True,
            universal_newlines=True,
            cwd=self.shared.cwd,
        )
        stripped = output.strip()
        lines = stripped.splitlines()
        line = lines[-1].replace("\\", "/")
        path = bytes(line, "ascii").decode("unicode-escape")
        self.shared.cwd = Path(path)

    def handle_perm_offset(self):
        for event in self.shared.events:
            if event.type == pygame.MOUSEWHEEL:
                self.perm_offset += event.y * self.SCROLL_SCALE

    def on_page_up(self):
        if self.shared.keys[pygame.K_LCTRL] and self.shared.keys[pygame.K_g]:
            self.perm_offset = 0

    def clear_prompts(self):
        self.copy_buttons.clear()
        self.prompts.clear()
        self.prompts.append(Prompt())
        self.current_prompt_index = 0

    def special_commands(self):
        if self.current_prompt.command in ("cls", "clear"):
            self.clear_prompts()
        elif self.current_prompt.command == "exit":
            exit()
        elif "cd" in self.current_prompt.command:
            self.change_directory()

    def on_release(self):
        if not self.current_prompt.released:
            return
        self.copy_buttons.append(CopyButton(self.current_prompt.output))
        self.prompts.append(Prompt())
        self.current_prompt_index += 1

    def update_copies(self):
        for btn in self.copy_buttons:
            btn.update()

    def update(self):
        self.current_prompt.update()
        self.special_commands()
        self.on_release()
        self.update_copies()
        self.handle_perm_offset()
        self.on_page_up()

    def draw(self):
        offset = 0
        for prompt, btn in itertools.zip_longest(self.prompts, self.copy_buttons):
            prompt.draw(offset + self.perm_offset)
            if btn is not None:
                btn.draw(offset + self.perm_offset)
            offset += prompt.full_surf.get_height() + 10

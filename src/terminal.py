import itertools
import os
import subprocess
from pathlib import Path

import pygame

from src.button import CopyButton
from src.data import DataManager
from src.prompt import Prompt
from src.shared import Shared


class Terminal:
    SCROLL_SCALE = 15

    def __init__(self) -> None:
        self.shared = Shared()
        self.shared.data = DataManager()
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
        if not self.current_prompt.released:
            return
        if self.current_prompt.command in ("cls", "clear"):
            self.clear_prompts()
        elif self.current_prompt.command == "exit":
            self.shared.data.on_exit()
            exit()
        elif "cd" in self.current_prompt.command:
            self.change_directory()

    def on_release(self):
        if not self.current_prompt.released:
            return
        self.shared.data.command_history.append(self.current_prompt.command)
        self.shared.data.current_index = len(self.shared.data.command_history)
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

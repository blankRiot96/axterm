import typing as t

import pygame

from src.settingstate import SettingState
from src.shared import Shared
from src.state_enums import State
from src.terminalstate import TerminalState
from src.utils import render_at, scale_image_perfect


class StateLike(t.Protocol):
    next_state: State | None

    def update(self):
        ...

    def draw(self):
        ...


class StateManager:
    def __init__(self) -> None:
        self.shared = Shared()
        self.state_dict: dict[State, StateLike] = {
            State.TERMINAL: TerminalState,
            State.SETTINGS: SettingState,
        }
        self.state_enum = State.TERMINAL
        self.state_obj: StateLike = self.state_dict.get(self.state_enum)()
        self.init_image_file()
        self.last_image_file = self.shared.data.image_file

    def init_image_file(self):
        if self.shared.data.image_file is not None:
            self.original_image = pygame.image.load(
                self.shared.data.image_file
            ).convert()
            self.image = scale_image_perfect(
                self.original_image, self.shared.screen.get_size()
            )
        else:
            self.image = None
        self.shared.resizing = False

    @property
    def state_enum(self) -> State:
        return self.__state_enum

    @state_enum.setter
    def state_enum(self, next_state: State) -> None:
        self.__state_enum = next_state
        self.state_obj: StateLike = self.state_dict.get(self.__state_enum)()

    def on_win_resize(self):
        self.shared.resizing = False
        for event in self.shared.events:
            if event.type == pygame.VIDEORESIZE:
                self.shared.resizing = True

    def update(self):
        self.on_win_resize()
        self.state_obj.update()

        if self.shared.data.image_file != self.last_image_file:
            self.init_image_file()

        if self.state_obj.next_state is not None:
            self.state_enum = self.state_obj.next_state

        if self.shared.resizing:
            self.image = scale_image_perfect(
                self.original_image, self.shared.screen.get_size()
            )

        self.last_image_file = self.shared.data.image_file

    def draw(self):
        if self.image is not None:
            render_at(self.shared.screen, self.image, "center")
        self.state_obj.draw()

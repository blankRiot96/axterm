import typing as t

import pygame

from src.controlstate import ControlState
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
            State.TERMINAL: TerminalState(),
            State.SETTINGS: SettingState(),
            State.CONTROLS: ControlState(),
        }
        self.state_enum = State.CONTROLS
        self.state_obj: StateLike = self.state_dict.get(self.state_enum)
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
        self.state_obj: StateLike = self.state_dict.get(self.__state_enum)

    def on_win_resize(self):
        self.shared.resizing = False
        for event in self.shared.events:
            if event.type == pygame.VIDEORESIZE:
                self.shared.resizing = True

    def on_ctrl_s(self):
        if self.shared.keys[pygame.K_LCTRL] and self.shared.keys[pygame.K_s]:
            self.state_obj.next_state = State.SETTINGS

    def on_ctrl_t(self):
        if self.shared.keys[pygame.K_LCTRL] and self.shared.keys[pygame.K_t]:
            self.state_obj.next_state = State.TERMINAL

    def on_ctrl_q(self):
        if self.shared.keys[pygame.K_LCTRL] and self.shared.keys[pygame.K_q]:
            self.state_obj.next_state = State.CONTROLS

    def fit_bg_image(self):
        if self.shared.resizing and self.image is not None:
            self.image = scale_image_perfect(
                self.original_image, self.shared.screen.get_size()
            )

        if self.shared.resizing:
            for obj in self.state_dict.values():
                if hasattr(obj, "on_win_resize"):
                    obj.on_win_resize()

    def update(self):
        self.on_ctrl_s()
        self.on_ctrl_q()
        self.on_ctrl_t()
        self.on_win_resize()
        self.fit_bg_image()
        self.state_obj.update()

        if self.shared.data.image_file != self.last_image_file:
            self.init_image_file()

        if self.state_obj.next_state is not None:
            self.state_enum = self.state_obj.next_state

        self.last_image_file = self.shared.data.image_file

    def draw(self):
        if self.image is not None:
            render_at(self.shared.screen, self.image, "center")
        self.state_obj.draw()

from typing import Self

import pygame


class Shared:
    _inst = None

    # Constants
    SCREEN_WIDTH, SCREEN_HEIGHT = (1024, 600)
    SRECT = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
    screen: pygame.Surface

    events: list[pygame.event.Event]
    dt: float

    def __new__(cls: type[Self], *args, **kwargs) -> Self:
        if Shared._inst is None:
            Shared._inst = super().__new__(cls)

        return Shared._inst

    def __init__(self, **kwargs) -> None:
        self.__dict__.update(kwargs)

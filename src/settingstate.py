from pathlib import Path

import pygame

from src.shared import Shared
from src.state_enums import State
from src.utils import Time, render_at, scale_image_perfect


class ImageBox:
    """Button to select"""

    BOX_SIZE = (220, 150)
    PADDING = 10

    def __init__(self, image: pygame.Surface, image_id: str, nth_box: int) -> None:
        self.shared = Shared()
        self.original_image = image
        self.image = pygame.Surface(self.BOX_SIZE)
        self.image.blit(scale_image_perfect(image, self.BOX_SIZE), (0, 0))
        self.image_id = image_id
        self.nth_box = nth_box
        self.get_grid_pos()
        self.get_screen_pos()
        self.click_timer = Time(0.1)
        self.click_highlight_done = True

        self.__overlay_alpha = 0
        self.overlay_surf = pygame.Surface(self.BOX_SIZE)

    @property
    def overlay_alpha(self):
        return self.__overlay_alpha

    @overlay_alpha.setter
    def overlay_alpha(self, value):
        if value > 100:
            value = 100
        if value < 0:
            value = 0
        self.__overlay_alpha = value

    def get_grid_pos(self):
        self.row = self.nth_box // 3
        self.col = self.nth_box % 3

    def get_screen_pos(self):
        self.pos = pygame.Vector2(
            self.col * (self.BOX_SIZE[0] + self.PADDING),
            self.row * (self.BOX_SIZE[1] + self.PADDING),
        )
        self.rect = self.image.get_rect(topleft=self.pos)

    def on_hover(self):
        if not self.hovering:
            self.overlay_alpha -= 300 * self.shared.dt
            return

        self.overlay_alpha += 300 * self.shared.dt

    def on_click(self):
        if not self.clicked:
            return

        self.click_timer.reset()
        self.click_highlight_done = False
        self.shared.data.config["image"] = self.image_id
        self.shared.data.config_image()

    def highlight_click(self):
        self.overlay_surf.fill("yellow")
        if self.click_timer.tick():
            self.overlay_surf.fill("black")
            self.click_highlight_done = True

    def update(self):
        self.hovering = self.rect.collidepoint(self.shared.mouse_pos - self.shared.diff)
        self.clicked = self.hovering and self.shared.clicked

        self.on_hover()
        self.on_click()

        self.overlay_surf.set_alpha(self.overlay_alpha)
        if not self.click_highlight_done:
            self.highlight_click()

    def draw(self, surf: pygame.Surface):
        surf.blit(self.image, self.pos)
        surf.blit(self.overlay_surf, self.pos)


class ImageSelector:
    """Grid selector to pick a background image
    for the terminal"""

    def __init__(self) -> None:
        self.shared = Shared()
        self.get_image_boxes()
        self.get_surf()
        self.shared.diff = pygame.Vector2(self.surf_rect.topleft)

    def get_surf(self):
        last_box = self.boxes[-1]
        width = (last_box.row + 1) * (ImageBox.BOX_SIZE[0] + ImageBox.PADDING)
        height = (last_box.col + 1) * (ImageBox.BOX_SIZE[1] + ImageBox.PADDING)
        self.surf = pygame.Surface((width, height), pygame.SRCALPHA)
        self.surf_rect = render_at(self.shared.screen, self.surf, "center")

    def get_image_boxes(self):
        image_paths = Path("assets/data/images").iterdir()
        images = [
            (pygame.image.load(path).convert(), path.name) for path in image_paths
        ]
        # TODO: Fix this shit
        """
        In order to fix "this shit", we have to look at what exactly is causing
        us the problem here.

        Q. Firstly, what do we want to achieve?
        A. We want an option for the user to set the background image to None.
           The CRS will then automatically not render a background image.
        
        Q. Secondly, how can we achieve this?
        A. To achieve this, we can allow the user to click on one of the image
           boxes to then re-config the image file. 

        Q. Finally, what is the problem here?
        A. The problem seems to be divided into 2 parts:
            (i) The mouse hovering seems to fucked
            (ii) It doesn't seem to support more than 3x3 grids 
        """
        # background_surf = pygame.Surface(ImageBox.BOX_SIZE)
        # background_surf.fill(self.shared.data.theme["background-color"])
        # render_at(background_surf, )
        # images.insert(0, (background_surf, None))
        self.boxes = [ImageBox(*image_pack, n) for n, image_pack in enumerate(images)]

    def update(self):
        for box in self.boxes:
            box.update()

    def draw(self):
        for box in self.boxes:
            box.draw(self.surf)
        self.surf_rect = render_at(self.shared.screen, self.surf, "center")


class OpacitySelector:
    """Slidebar to toggle opacity for terminal
    Interval: [0.2, 1.0]
    """


class ThemeSelector:
    """Dropbox(?) to pick appropriate theme"""


class SettingState:
    def __init__(self) -> None:
        self.shared = Shared()
        self.next_state: State | None = None
        self.image_selector = ImageSelector()

    def on_ctrl_t(self):
        if self.shared.keys[pygame.K_LCTRL] and self.shared.keys[pygame.K_t]:
            self.next_state = State.TERMINAL

    def update(self):
        self.image_selector.update()
        self.on_ctrl_t()

    def draw(self):
        self.image_selector.draw()
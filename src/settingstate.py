import json
from pathlib import Path

import pygame

from src.shared import Shared
from src.slider import HorizontalSlider
from src.state_enums import State
from src.utils import Time, get_font, render_at, scale_image_perfect


class ImageBox:
    """Button to select"""

    BOX_SIZE = (220, 150)
    PADDING = 10
    N_ROWS = 3

    def __init__(
        self, image: pygame.Surface, image_id: None | str, nth_box: int
    ) -> None:
        self.shared = Shared()
        self.image = pygame.Surface(self.BOX_SIZE)
        render_at(self.image, scale_image_perfect(image, self.BOX_SIZE), "center")
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
        self.row = self.nth_box // ImageBox.N_ROWS
        self.col = self.nth_box % ImageBox.N_ROWS

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


class DefaultBox(ImageBox):
    FONT = get_font("assets/fonts/regular1.ttf", 16)

    def __init__(self) -> None:
        image = pygame.Surface(ImageBox.BOX_SIZE)
        super().__init__(image, None, 0)
        self.image.fill(self.shared.data.theme["background-color"])
        pygame.draw.rect(
            self.image, "yellow", pygame.Rect((0, 0), ImageBox.BOX_SIZE), 5
        )
        render_at(
            self.image,
            self.FONT.render("default", True, self.shared.data.theme["text-color"]),
            "center",
        )


class ImageSelector:
    """Grid selector to pick a background image
    for the terminal"""

    def __init__(self) -> None:
        self.shared = Shared()

    def post_init(self):
        self.get_image_boxes()
        self.get_surf()
        self.shared.diff = pygame.Vector2(self.surf_rect.topleft)

    def get_surf(self):
        last_box = self.boxes[-1]
        width = ImageBox.N_ROWS * (ImageBox.BOX_SIZE[0] + ImageBox.PADDING)
        height = (last_box.row + 1) * (ImageBox.BOX_SIZE[1] + ImageBox.PADDING)
        self.surf = pygame.Surface((width, height), pygame.SRCALPHA)
        self.surf_rect = render_at(self.shared.screen, self.surf, "center")

    def get_image_boxes(self):
        image_paths = Path("assets/data/images").iterdir()
        images = (
            (pygame.image.load(path).convert(), path.name) for path in image_paths
        )
        self.boxes = [DefaultBox()]
        self.boxes.extend(
            ImageBox(*image_pack, n + 1) for n, image_pack in enumerate(images)
        )

    def update(self):
        for box in self.boxes:
            box.update()
        self.shared.diff = pygame.Vector2(self.surf_rect.topleft)

    def draw(self):
        for box in self.boxes:
            box.draw(self.surf)
        self.surf_rect = render_at(self.shared.screen, self.surf, "center")


class OpacitySelector:
    """Slidebar to toggle opacity for terminal
    Interval: [0.2, 1.0]
    """

    def __init__(self) -> None:
        self.shared = Shared()
        center = self.shared.screen.get_rect().center
        self.slider_rect = pygame.Rect(0, 0, 300, 100)
        self.slider_rect.center = center
        self.slider = HorizontalSlider(
            self.slider_rect,
            bg_color=self.shared.data.theme["text-color"],
            fg_color=self.shared.data.theme["background-color"],
            min_value=0.2,
            max_value=1.0,
            step=0.01,
            callback=self.on_slide,
        )

    def on_slide(self, value):
        self.shared.win.opacity = value
        self.shared.data.config["opacity"] = value

    def on_win_resize(self):
        center = self.shared.screen.get_rect().center
        self.slider.rail.center = center
        self.slider.x, self.slider.y = center

    def update(self):
        self.slider.update(self.shared.events)

        if self.shared.resizing:
            self.on_win_resize()

    def draw(self):
        self.slider.draw(self.shared.screen)


class ThemeBox:
    FONT = get_font("assets/fonts/bold1.ttf", 16)
    BOX_SIZE = (220, 150)
    PADDING = 10
    N_ROWS = 3

    def __init__(self, theme: dict, theme_name: str, nth_box: int) -> None:
        self.shared = Shared()
        self.theme = theme
        self.name = theme_name
        self.nth_box = nth_box

        self.get_image()
        self.get_grid_pos()
        self.get_screen_pos()

        self.clicked = False
        self.click_timer = Time(0.1)
        self.click_highlight_done = True

        self.__overlay_alpha = 0
        self.overlay_surf = pygame.Surface(self.BOX_SIZE)

    def get_image(self):
        self.image = pygame.Surface(self.BOX_SIZE)
        self.image.fill(self.theme["background-color"])
        name_surf = self.FONT.render(self.name, True, self.theme["text-color"])
        render_at(self.image, name_surf, "center")

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
        self.row = self.nth_box // ImageBox.N_ROWS
        self.col = self.nth_box % ImageBox.N_ROWS

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
        self.shared.data.theme = self.theme
        self.shared.data.config["theme"] = self.name

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


class ThemeSelector:
    """Grid to pick appropriate theme"""

    FONT = get_font("assets/fonts/regular1.ttf", 16)

    def __init__(self) -> None:
        self.shared = Shared()
        self.get_theme_boxes()
        self.get_surf()
        self.text_init()
        self.shared.diff = pygame.Vector2(self.surf_rect.topleft)

    def text_init(self):
        self.text_surf = self.FONT.render(
            f"Theme Selected: {self.shared.data.config['theme']}",
            True,
            self.shared.data.theme["background-color"],
            self.shared.data.theme["text-color"],
        )

    def get_surf(self):
        last_box = self.boxes[-1]
        width = ImageBox.N_ROWS * (ImageBox.BOX_SIZE[0] + ImageBox.PADDING)
        height = (last_box.row + 1) * (ImageBox.BOX_SIZE[1] + ImageBox.PADDING)
        self.surf = pygame.Surface((width, height), pygame.SRCALPHA)
        self.surf_rect = render_at(self.shared.screen, self.surf, "center")

    def get_theme_boxes(self):
        theme_paths = Path("assets/data/themes").iterdir()
        self.boxes = []
        for n, path in enumerate(theme_paths):
            with open(path) as f:
                self.boxes.append(ThemeBox(json.load(f), path.name, n))

    def update(self):
        for box in self.boxes:
            if box.clicked:
                self.text_init()
            box.update()
        self.shared.diff = pygame.Vector2(self.surf_rect.topleft)

    def draw(self):
        render_at(
            self.shared.screen,
            self.text_surf,
            "midtop",
            offset=(0, Button.SIZE[1] + 20),
        )
        for box in self.boxes:
            box.draw(self.surf)
        self.surf_rect = render_at(self.shared.screen, self.surf, "center")


class Button:
    SIZE = (70, 20)
    FONT = get_font("assets/fonts/regular1.ttf", 12)

    def __init__(self, name: str, pos: int) -> None:
        self.shared = Shared()
        self.name = name
        self.pos = pos
        self.get_positional_rect()
        self.image = pygame.Surface((self.SIZE))
        self.image.fill(self.shared.data.theme["text-color"])
        render_at(
            self.image,
            self.FONT.render(
                self.name, True, self.shared.data.theme["background-color"]
            ),
            "center",
        )
        self.click_timer = Time(0.1)
        self.click_highlight_done = True
        self.clicked = False

        self.__overlay_alpha = 0
        self.overlay_surf = pygame.Surface(self.SIZE)

    def get_positional_rect(self):
        self.rect = pygame.Rect((0, 0), self.SIZE)
        self.rect.midtop = (
            self.shared.screen.get_rect().midtop[0] - self.SIZE[0],
            self.shared.screen.get_rect().midtop[1],
        )

        self.rect.x += self.SIZE[0] * self.pos

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

    def highlight_click(self):
        self.overlay_surf.fill("yellow")
        if self.click_timer.tick():
            self.overlay_surf.fill("black")
            self.click_highlight_done = True

    def update(self):
        self.hovering = self.rect.collidepoint(self.shared.mouse_pos)
        self.clicked = self.hovering and self.shared.clicked

        self.on_hover()
        self.on_click()

        self.overlay_surf.set_alpha(self.overlay_alpha)
        if not self.click_highlight_done:
            self.highlight_click()

    def draw(self):
        self.shared.screen.blit(self.image, self.rect)
        self.shared.screen.blit(self.overlay_surf, self.rect)


class SettingState:
    def __init__(self) -> None:
        self.shared = Shared()
        self.next_state: State | None = None
        self.settings = {
            "Image": ImageSelector(),
            "Theme": ThemeSelector(),
            "Opacity": OpacitySelector(),
        }
        self.current_setting = self.settings["Image"]
        self.buttons = (
            Button("Image", 0),
            Button("Theme", 1),
            Button("Opacity", 2),
        )
        self.first_load = True

    def update_buttons(self):
        for button in self.buttons:
            if self.shared.resizing:
                button.get_positional_rect()

            if button.clicked:
                self.current_setting = self.settings.get(button.name)
            button.update()

    def on_win_resize(self):
        for button in self.buttons:
            button.get_positional_rect()
        for setting in self.settings.values():
            if hasattr(setting, "on_win_resize"):
                setting.on_win_resize()

    def update(self):
        if self.first_load:
            self.settings["Image"].post_init()
            self.first_load = False
        self.current_setting.update()
        self.update_buttons()

        if self.shared.resizing:
            self.on_win_resize()

    def draw(self):
        if self.first_load:
            self.settings["Image"].post_init()
            self.first_load = False
        self.current_setting.draw()
        for button in self.buttons:
            button.draw()

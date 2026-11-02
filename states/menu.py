# states/main_menu.py
import pyray as rl
from game import Game
from states.base import State


class MainMenuState(State):
    """Title screen with a small vertical list of buttons."""
    def __init__(self, game: Game, data=None) -> None:
        super().__init__(game, data)
        self._hovered: int = -1
        self._built:   bool = False

    # (label, callback-name) — we resolve the callback at click time so
    # subclasses/instances can override.
    ITEMS = [
        ("Play",   "_on_play"),
        ("Options","_on_options"),
        ("Quit",   "_on_quit"),
    ]

    def enter(self) -> None:
        self._hovered: int = -1
        self._built:   bool = False

    def _build_layout(self, screen_w: int, screen_h: int) -> None:
        btn_w, btn_h, gap = 260.0, 56.0, 14.0
        total_h = len(self.ITEMS) * btn_h + (len(self.ITEMS) - 1) * gap
        x = (screen_w - btn_w) / 2.0
        y0 = (screen_h - total_h) / 2.0 + 40.0

        self._buttons: list[rl.Rectangle] = [
            rl.Rectangle(x, y0 + i * (btn_h + gap), btn_w, btn_h)
            for i in range(len(self.ITEMS))
        ]
        self._title_pos = rl.Vector2(screen_w / 2.0, y0 - 120.0)
        self._built = True
        self._screen = (screen_w, screen_h)

    def update(self, dt: float) -> None:
        sw, sh = rl.get_screen_width(), rl.get_screen_height()
        if not self._built or self._screen != (sw, sh):
            self._build_layout(sw, sh)

        mouse = rl.get_mouse_position()
        self._hovered = -1
        for i, rect in enumerate(self._buttons):
            if rl.check_collision_point_rec(mouse, rect):
                self._hovered = i
                break

        if rl.is_mouse_button_pressed(rl.MouseButton.MOUSE_BUTTON_LEFT) and self._hovered >= 0:
            label, cb_name = self.ITEMS[self._hovered]
            getattr(self, cb_name)()

        if rl.is_key_pressed(rl.KeyboardKey.KEY_ESCAPE):
            self._on_quit()

    def render(self, logical_texture: rl.RenderTexture) -> None:
        rl.clear_background(rl.Color(16, 20, 28, 255))
        if not self._built:
            return

        title = "MATHCARDS"
        tw = rl.measure_text(title, 64)
        rl.draw_text(title,
                     int(self._title_pos.x - tw / 2),
                     int(self._title_pos.y - 64),
                     64, rl.WHITE)

        mouse = rl.get_mouse_position()
        for i, (label, _) in enumerate(self.ITEMS):
            rect    = self._buttons[i]
            hovered = (i == self._hovered)
            bg      = rl.Color(40, 55, 80, 255) if hovered else rl.Color(26, 32, 44, 255)
            border  = rl.Color(120, 160, 240, 255) if hovered else rl.Color(70, 85, 115, 200)

            rl.draw_rectangle_rounded(rect, 0.25, 8, bg)
            rl.draw_rectangle_rounded_lines_ex(rect, 0.25, 8, 1.5, border)

            lw = rl.measure_text(label, 24)
            rl.draw_text(label,
                         int(rect.x + (rect.width - lw) / 2),
                         int(rect.y + (rect.height - 24) / 2),
                         24, rl.WHITE)

    # --- callbacks (override or replace as you wire real state transitions) ---

    def _on_play(self) -> None:
        # e.g. self.request_push(InGameState())
        print("PLAY pressed")

    def _on_options(self) -> None:
        # e.g. self.request_push(InGameMenuState())
        print("OPTIONS pressed")

    def _on_quit(self) -> None:
        # e.g. self.request_quit()
        rl.close_window()


class InGameMenuState(State):
    """Pause overlay: dim background + Resume / Main Menu buttons."""

    ITEMS = [
        ("Resume",    "_on_resume"),
        ("Main Menu", "_on_main_menu"),
    ]

    def enter(self) -> None:
        self._hovered: int = -1
        self._built:   bool = False

    def _build_layout(self, screen_w: int, screen_h: int) -> None:
        btn_w, btn_h, gap = 240.0, 52.0, 12.0
        total_h = len(self.ITEMS) * btn_h + (len(self.ITEMS) - 1) * gap
        x = (screen_w - btn_w) / 2.0
        y0 = (screen_h - total_h) / 2.0

        self._buttons: list[rl.Rectangle] = [
            rl.Rectangle(x, y0 + i * (btn_h + gap), btn_w, btn_h)
            for i in range(len(self.ITEMS))
        ]
        self._screen = (screen_w, screen_h)
        self._built = True

    def update(self, dt: float) -> None:
        sw, sh = rl.get_screen_width(), rl.get_screen_height()
        if not self._built or self._screen != (sw, sh):
            self._build_layout(sw, sh)

        mouse = rl.get_mouse_position()
        self._hovered = -1
        for i, rect in enumerate(self._buttons):
            if rl.check_collision_point_rec(mouse, rect):
                self._hovered = i
                break

        if rl.is_mouse_button_pressed(rl.MouseButton.MOUSE_BUTTON_LEFT) and self._hovered >= 0:
            getattr(self, self.ITEMS[self._hovered][1])()

        if rl.is_key_pressed(rl.KeyboardKey.KEY_ESCAPE):
            self._on_resume()

    def render(self, logical_texture: rl.RenderTexture) -> None:
        # Dim overlay — the underlying game state should have rendered already
        # if your stack renders lower states below this one.
        sw, sh = rl.get_screen_width(), rl.get_screen_height()
        rl.draw_rectangle(0, 0, sw, sh, rl.Color(0, 0, 0, 160))

        title = "PAUSED"
        tw = rl.measure_text(title, 48)
        rl.draw_text(title,
                     int((sw - tw) / 2),
                     int(self._buttons[0].y - 90),
                     48, rl.WHITE)

        for i, (label, _) in enumerate(self.ITEMS):
            rect    = self._buttons[i]
            hovered = (i == self._hovered)
            bg      = rl.Color(40, 55, 80, 255) if hovered else rl.Color(26, 32, 44, 230)
            border  = rl.Color(120, 160, 240, 255) if hovered else rl.Color(70, 85, 115, 200)

            rl.draw_rectangle_rounded(rect, 0.25, 8, bg)
            rl.draw_rectangle_rounded_lines_ex(rect, 0.25, 8, 1.5, border)

            lw = rl.measure_text(label, 22)
            rl.draw_text(label,
                         int(rect.x + (rect.width - lw) / 2),
                         int(rect.y + (rect.height - 22) / 2),
                         22, rl.WHITE)

    def _on_resume(self) -> None:
        # e.g. self.request_pop()
        print("RESUME pressed")

    def _on_main_menu(self) -> None:
        # e.g. self.request_replace(MainMenuState())
        print("MAIN MENU pressed")
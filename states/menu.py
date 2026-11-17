# states/main_menu.py
import pyray as rl

from entities.ui.button import UIButton
from state_manager import StateManager
from states.base import State
from states.deck_builder import DeckBuilderState
from states.game import MatchState


class MainMenuState(State):
    """Title screen with a small vertical list of buttons."""
    def __init__(self, game: StateManager, data=None) -> None:
        super().__init__(game, data)
        self._buttons: list[UIButton] = []
        self._built:   bool = False
        self.match_state = MatchState(self.game)

    # (label, callback-name) — we resolve the callback at click time so
    # subclasses/instances can override.
    ITEMS = [
        ("Play",   "_on_play"),
        ("Build Deck", "_on_build_deck"),
        ("Options","_on_options"),
        ("Quit",   "_on_quit"),
    ]

    def enter(self) -> None:
        self._built: bool = False

    def _build_layout(self, screen_w: int, screen_h: int) -> None:
        btn_w, btn_h, gap = 260.0, 56.0, 14.0
        total_h = len(self.ITEMS) * btn_h + (len(self.ITEMS) - 1) * gap
        x = (screen_w - btn_w) / 2.0
        y0 = (screen_h - total_h) / 2.0 + 40.0

        self._buttons = []
        for i, (label, _) in enumerate(self.ITEMS):
            rect = rl.Rectangle(x, y0 + i * (btn_h + gap), btn_w, btn_h)
            # Note: Passing a base dark color since UIButton handles hover lightening
            btn = UIButton(label, rect, self.game.font, rl.Color(26, 32, 44, 255))
            self._buttons.append(btn)
            
        self._title_pos = rl.Vector2(screen_w / 2.0, y0 - 120.0)
        self._built = True
        self._screen = (screen_w, screen_h)

    def update(self, dt: float) -> None:
        sw, sh = rl.get_screen_width(), rl.get_screen_height()
        if not self._built or self._screen != (sw, sh):
            self._build_layout(sw, sh)

        for i, btn in enumerate(self._buttons):
            btn.update(dt)
            if btn.is_clicked:
                _, cb_name = self.ITEMS[i]
                getattr(self, cb_name)()
                return

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

        for btn in self._buttons:
            btn.render(logical_texture)

    # --- callbacks (override or replace as you wire real state transitions) ---

    def _on_play(self) -> None:
        # print("PLAY pressed")
        self.game.enter_state(self.match_state)

    def _on_build_deck(self) -> None:
        # print("BUILD DECK pressed")
        self.game.enter_state(DeckBuilderState(self.game))

    def _on_options(self) -> None:
        print("OPTIONS pressed")

    def _on_quit(self) -> None:
        rl.close_window()


class InGameMenuState(State):
    """Pause overlay: dim background + Resume / Main Menu buttons."""

    ITEMS = [
        ("Resume",    "_on_resume"),
        ("Main Menu", "_on_main_menu"),
    ]

    def __init__(self, game: StateManager, data=None) -> None:
        super().__init__(game, data)
        self._buttons: list[UIButton] = []
        self._built: bool = False

    def enter(self) -> None:
        self._built = False

    def _build_layout(self, screen_w: int, screen_h: int) -> None:
        btn_w, btn_h, gap = 240.0, 52.0, 12.0
        total_h = len(self.ITEMS) * btn_h + (len(self.ITEMS) - 1) * gap
        x = (screen_w - btn_w) / 2.0
        y0 = (screen_h - total_h) / 2.0

        self._buttons = []
        for i, (label, _) in enumerate(self.ITEMS):
            rect = rl.Rectangle(x, y0 + i * (btn_h + gap), btn_w, btn_h)
            btn = UIButton(label, rect, self.game.font, rl.Color(26, 32, 44, 230))
            self._buttons.append(btn)
            
        self._screen = (screen_w, screen_h)
        self._built = True

    def update(self, dt: float) -> None:
        sw, sh = rl.get_screen_width(), rl.get_screen_height()
        if not self._built or self._screen != (sw, sh):
            self._build_layout(sw, sh)

        for i, btn in enumerate(self._buttons):
            btn.update(dt)
            if btn.is_clicked:
                getattr(self, self.ITEMS[i][1])()
                return

        if rl.is_key_pressed(rl.KeyboardKey.KEY_ESCAPE):
            self._on_resume()

    def render(self, logical_texture: rl.RenderTexture) -> None:
        sw, sh = rl.get_screen_width(), rl.get_screen_height()
        rl.draw_rectangle(0, 0, sw, sh, rl.Color(0, 0, 0, 160))

        if not self._built:
            return

        title = "PAUSED"
        tw = rl.measure_text(title, 48)
        rl.draw_text(title,
                     int((sw - tw) / 2),
                     int(self._buttons[0].rect.y - 90),
                     48, rl.WHITE)

        for btn in self._buttons:
            btn.render(logical_texture)

    def _on_resume(self) -> None:
        print("RESUME pressed")

    def _on_main_menu(self) -> None:
        print("MAIN MENU pressed")
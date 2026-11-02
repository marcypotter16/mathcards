import os
from states.base import State

import pyray as rl

import Settings
from tfr import TypstFormulaRenderer


class Game:
    def __init__(self, data={}) -> None:
        self.state_stack: list[State] = []
        self.tfr: TypstFormulaRenderer = data.get("tfr")
        self.font: rl.Font = rl.get_font_default()

    def init(self) -> None:
        """To be called after raylib initialization"""
        font_path = getattr(Settings, "FONT_PATH", "")
        if font_path and os.path.exists(font_path):
            loaded = rl.load_font_ex(font_path, 64, None, 0)
            if loaded.texture.id > 0:
                self.font = loaded
                rl.set_texture_filter(self.font.texture, rl.TextureFilter.TEXTURE_FILTER_BILINEAR)
        else:
            self.font = rl.get_font_default()

    def enter_state(self, new_state: State) -> None:
        self.state_stack.append(new_state)

    def exit_state(self) -> None:
        self.state_stack.pop()

    def update(self, dt: float):
        if len(self.state_stack) == 0:
            return
        self.state_stack[-1].update(dt)

    def render(self, logical_texture: rl.RenderTexture | None = None) -> None:
        if len(self.state_stack) == 0:
            return
        self.state_stack[-1].render(logical_texture)

    def unload(self):
        if len(self.state_stack) != 0:
            self.state_stack[-1].unload()
        if hasattr(self, "font") and self.font.texture.id != rl.get_font_default().texture.id:
            rl.unload_font(self.font)

from typing import TYPE_CHECKING

import pyray as rl

if TYPE_CHECKING:
    from game import Game

class State:
    def __init__(self, game: 'Game', data=None) -> None:
        """Data is what a previous state can pass to this state."""
        self.data = data
        self.game = game

    def update(self, dt: float) -> None:
        pass

    def render(self, logical_texture: rl.RenderTexture | None = None) -> None:
        pass

    def unload(self):
        pass
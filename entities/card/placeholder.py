from pyray import RenderTexture

from entities.card.base import BaseCard

import pyray as rl

from mathematics.vector import Vector2


class PlaceholderCard(BaseCard):
    def __init__(self, center: Vector2, flipped=True) -> None:
        super().__init__()
        self.center = center
        self.flipped = flipped
        self.back_tex = rl.load_texture("assets/backs/back_0.png")

    def update(self, dt):
        return super().update(dt)

    def render(self, logical_texture: RenderTexture | None):
        tex = self.back_tex
        topleft = self.center - .5 * self.DIMENSIONS
        dest = rl.Rectangle(topleft.x, topleft.y, self.DIMENSIONS.x, self.DIMENSIONS.y)
        source = rl.Rectangle(0, 0, tex.width, tex.height)
        rl.draw_texture_pro(tex, source, dest, (0, 0), 0.0, rl.WHITE)
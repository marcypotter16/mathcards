import pyray as rl
from pyray import RenderTexture

from entities.card.base import BaseCard
from mathematics.vector import Vector2
from shaders.shaders import Shaders


class PlaceholderCard(BaseCard):
    def __init__(self, center: Vector2, flipped=True) -> None:
        super().__init__()
        self.center = center
        self.center_rest = center
        self.flipped = flipped
        self.back_tex = rl.load_texture("assets/backs/orbit.png")

    def update(self, dt):
        return super().update(dt)

    def render(self, logical_texture: RenderTexture | None):
        Shaders.card_visuals.draw(self)

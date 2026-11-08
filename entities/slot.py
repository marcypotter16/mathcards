from entities.base import Entity
from entities.card.base import BaseCard
from mathematics.vector import Vector2

# TODO IMPLEMENT SWAP TWO CARD SLOTS (USEFUL FOR CHAIN REACTIONS)

import pyray as rl


class Slot(Entity):

    DIMENSIONS  = Vector2(150, 225)
    PADDING     = 10

    def __init__(self) -> None:
        super().__init__()
        self.center:        Vector2             = Vector2(0, 0)
        self.rec:           rl.Rectangle        = rl.Rectangle()
        self.color:         rl.Color            = rl.RAYWHITE

        self.content:       BaseCard | None     = None

    def put_card(self, card: BaseCard) -> bool:
        if self.content is not None:
            return False
        self.content = card
        if card.rotation != 0:
            card.tween_rotation(0.0)
        if card.scale != 1.0:
            card.tween_scale(1.0)
        card.tween_center(self.center, callback=lambda: card.place_card(self.center))
        return True

    def place_topleft(self, new_topleft: Vector2):
        # The visual box starts at new_topleft.
        # The inner dimensions start at new_topleft + PADDING.
        # So the center is at new_topleft + PADDING + DIMENSIONS/2.
        self.place_center(new_topleft + Vector2(self.PADDING, self.PADDING) + .5 * self.DIMENSIONS)

    def place_center(self, new_center: Vector2):
        self.center = new_center
        self.rec = rl.Rectangle(
            self.center.x - self.DIMENSIONS.x / 2 - self.PADDING,
            self.center.y - self.DIMENSIONS.y / 2 - self.PADDING,
            self.DIMENSIONS.x + self.PADDING * 2,
            self.DIMENSIONS.y + self.PADDING * 2
        )

    def set_color(self, new_color: rl.Color):
        self.color = new_color

    def is_free(self) -> bool:
        return self.content is None

    def update(self, dt: float) -> None:
        super().update(dt)
        if self.content is not None:
            self.content.update(dt)

    def render(self, logical_texture) -> None:
        rl.draw_rectangle_rounded_lines(self.rec, 0.02, 0, self.color)
        if self.content is not None:
            self.content.render(logical_texture)

import random

import pyray as rl

from entities.base import Entity
from entities.card.base import BaseCard
from entities.game_manager.actions import CardToDiscardPileAction, DiscardPileOpenDetail
from entities.game_manager.dataclasses import GameView
from entities.game_manager.events import EVENT_BUS
from entities.player import PlayerId, PlayerView
from mathematics.vector import Vector2


class DiscardPileManager(Entity):
    def __init__(self, center: Vector2, gw: GameView, owner: PlayerId) -> None:
        super().__init__()
        self.center = center
        self.owner = owner
        self.d = BaseCard.DIMENSIONS
        self.discard = gw.players[owner].discard
        self.rect = rl.Rectangle(
            int(self.center.x - .5 * self.d.x),
            int(self.center.y - .5 * self.d.y),
            self.d.x,
            self.d.y
        )
        self.tex = rl.load_texture("assets/discard.png")
        rl.set_texture_filter(self.tex, rl.TextureFilter.TEXTURE_FILTER_BILINEAR)
        self.stack_size = 10
        self.rotations = [random.uniform(-6, 6) for _ in range(self.stack_size)]
        self.origins = [rl.Vector2(random.uniform(0, self.d.x), random.uniform(0, self.d.y)) for _ in range(self.stack_size)]
        self.tex_rect = rl.Rectangle(
            0, 0, self.tex.width, self.tex.height
        )

    def sync(self, pw: PlayerView):
        self.discard = pw.discard

    def update(self, dt: float) -> None:
        # IF RIGHT CLICK
        mp = rl.is_mouse_button_pressed(rl.MouseButton.MOUSE_BUTTON_RIGHT)
        mouse = rl.get_mouse_position()
        if mp:
            if rl.check_collision_point_rec(mouse, self.rect):
                EVENT_BUS.emit(DiscardPileOpenDetail(self.discard))

    def render(self, logical_texture: rl.RenderTexture | None) -> None:
            rl.draw_texture_pro(
                self.tex,
                self.tex_rect,
                self.rect,
                # rl.Vector2(self.back_tex.width / 2, self.back_tex.height / 2),
                rl.vector2_zero(),
                0.0,
                # self.origins[i],
                # self.rotations[i],
                rl.WHITE
            )
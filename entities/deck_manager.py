import random

from pyray import RenderTexture

from cached import Cache
from entities.base import Entity
from entities.game_manager.actions import DrawCardAction
from entities.game_manager.dataclasses import PlayerView
from entities.game_manager.events import EVENT_BUS
from state_manager import StateManager
from mathematics.vector import Vector2

import pyray as rl

class DeckManager(Entity):
    
    DIMENSIONS = Vector2(150, 225)

    def __init__(self, center: Vector2, sm: StateManager, player_view: PlayerView) -> None:
        super().__init__()
        self.sm = sm
        self.event_bus = EVENT_BUS
        self.center = center
        self.back_tex = Cache.card_back
        assert self.back_tex is not None
        self.back_tex_rect = rl.Rectangle(0, 0, self.back_tex.width, self.back_tex.height)
        self.stack_size = 10
        self.rotations = [random.uniform(-6, 6) for _ in range(self.stack_size)]
        self.origins = [rl.Vector2(random.uniform(0, self.DIMENSIONS.x), random.uniform(0, self.DIMENSIONS.y)) for _ in range(self.stack_size)]
        self.pw = player_view

        self.deck_size_label_rect = rl.Rectangle(self.rect.x, self.rect.y - 50, self.rect.width, 40)

    @property
    def rect(self) -> rl.Rectangle:
        return rl.Rectangle(
            self.center.x - self.DIMENSIONS.x * .5,
            self.center.y - self.DIMENSIONS.y * .5,
            self.DIMENSIONS.x,
            self.DIMENSIONS.y
        )

    def sync(self, new_pw: PlayerView):
        self.pw = new_pw

    def update(self, dt: float) -> None:
        clicked = rl.is_mouse_button_released(rl.MouseButton.MOUSE_BUTTON_LEFT)
        mouse_pos = rl.get_mouse_position()
        if rl.check_collision_point_rec(mouse_pos, self.rect):
            self._visible_deck_size_label = True
            if clicked:
                if self.pw.hand is None:
                    print(f"Deck is not mine, can only show size: {23}")
                    return
                print(f"Clicked on deck with permissions, emitting draw action...")
                self.event_bus.emit(DrawCardAction(self.pw.viewer))
        else:
            self._visible_deck_size_label = False

    def render(self, logical_texture: RenderTexture | None) -> None:
        assert self.back_tex is not None
        # rl.draw_rectangle_rec(self.rect, rl.RED)
        for i in range(self.stack_size):
            r = rl.Rectangle(
                self.origins[i].x + self.center.x - self.DIMENSIONS.x * .5, 
                self.origins[i].y + self.center.y - self.DIMENSIONS.y * .5, 
                self.DIMENSIONS.x, 
                self.DIMENSIONS.y)
            rl.draw_texture_pro(
                self.back_tex,
                self.back_tex_rect,
                r,
                # rl.Vector2(self.back_tex.width / 2, self.back_tex.height / 2),
                # rl.vector2_zero(),
                self.origins[i],
                self.rotations[i],
                rl.WHITE
            )
        if self._visible_deck_size_label:
            measure = Vector2(vect=rl.measure_text_ex(self.sm.font, f"{self.pw.deck_size}", 36, 0))
            rl.draw_text_ex(self.sm.font, f"{self.pw.deck_size}", (self.center - measure * .5).raylib_ref, 36, 0, rl.WHITE)
"""Small state for isolating first-use card rendering during a draw."""

from typing import TYPE_CHECKING

import pyray as rl

from draw_debug import arm_draw_trace, draw_debug
from entities.card.spell_card import SpellCard
from mathematics.vector import Vector2
from Settings import WINDOW
from states.base import State
from test import make_game_state2

if TYPE_CHECKING:
    from state_manager import StateManager


class RendererTestState(State):
    """Shows three slot outlines and one cached SpellCard, with a bake toggle.

    Controls:
      D: draw the cached test card
      P: toggle baking the card before the slot/scene pass
      R: reset the card's GPU textures so the draw can be repeated
      Esc: return to the previous state
    """

    def __init__(self, game: StateManager, data=None) -> None:
        super().__init__(game, data)
        self.lw = WINDOW["L_WIDTH"]
        self.lh = WINDOW["L_HEIGHT"]

        # Use the same startup-created card objects and queued Typst work as a match.
        self.gs = make_game_state2(game)
        deck_ids = self.gs.players["p1"].deck.cards
        self.card = next(
            self.gs.cards[cid]
            for cid in reversed(deck_ids)
            if isinstance(self.gs.cards[cid], SpellCard)
        )

        self.drawn = False
        self.prebake_before_scene = False
        self.card_start = Vector2(220, self.lh * 0.78)
        self.card_target = Vector2(self.lw * 0.5, self.lh * 0.78)
        self.slot_y = self.lh * 0.43
        self.slot_width = 170
        self.slot_height = 245

    def update(self, dt: float) -> None:
        if rl.is_key_pressed(rl.KeyboardKey.KEY_ESCAPE):
            self.game.exit_state()
            return

        if rl.is_key_pressed(rl.KeyboardKey.KEY_P):
            self.prebake_before_scene = not self.prebake_before_scene

        if rl.is_key_pressed(rl.KeyboardKey.KEY_R):
            self._reset_card()

        if rl.is_key_pressed(rl.KeyboardKey.KEY_D) and not self.drawn:
            self.card.place_card(self.card_start)
            self.card.tween_center(self.card_target, dur=0.4)
            self.drawn = True
            arm_draw_trace()
            draw_debug(
                "RendererTestState draw",
                f"card={self.card.card_id}",
                f"prebake_before_scene={self.prebake_before_scene}",
            )

        if self.drawn:
            self.card.update(dt)

    def _reset_card(self) -> None:
        if self.card.tex is not None:
            rl.unload_texture(self.card.tex)
            self.card.tex = None
        if self.card.render_texture is not None:
            rl.unload_render_texture(self.card.render_texture)
            self.card.render_texture = None

        self.card.texture_is_dirty = True
        self.card.tm.tweens.clear()
        self.card.place_card(self.card_start)
        self.drawn = False
        draw_debug("RendererTestState reset", f"card={self.card.card_id}")

    def render(self, logical_texture: rl.RenderTexture | None = None) -> None:
        if self.drawn and self.prebake_before_scene and self.card.texture_is_dirty:
            draw_debug("RendererTestState prebaking before scene", f"card={self.card.card_id}")
            self.card.bake_texture()
            if logical_texture is not None:
                rl.begin_texture_mode(logical_texture)
                draw_debug("RendererTestState logical target restored")

        # Three empty slot outlines are enough to reveal a frame-wide render flash.
        for index in range(3):
            x = self.lw * 0.5 + (index - 1) * (self.slot_width + 24) - self.slot_width * 0.5
            rect = rl.Rectangle(x, self.slot_y - self.slot_height * 0.5, self.slot_width, self.slot_height)
            rl.draw_rectangle_rounded_lines(rect, 0.04, 4, rl.RAYWHITE)

        font = self.game.font
        mode = "PREBAKE BEFORE SCENE" if self.prebake_before_scene else "BAKE DURING CARD RENDER"
        rl.draw_text_ex(font, f"Renderer test: {mode}", rl.Vector2(40, 40), 28, 1, rl.WHITE)
        rl.draw_text_ex(
            font,
            "D draw cached card | P toggle bake mode | R reset textures | Esc back",
            rl.Vector2(40, 78),
            20,
            1,
            rl.LIGHTGRAY,
        )

        if self.drawn:
            self.card.render(logical_texture)


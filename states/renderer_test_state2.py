"""Small state for isolating first-use card rendering during a draw."""

from typing import TYPE_CHECKING

from entities.card.placeholder import PlaceholderCard
from mathematics.vector import Vector2
from Settings import WINDOW
from states.base import State

if TYPE_CHECKING:
    from state_manager import StateManager


class RendererTestState2(State):
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

        self.center = Vector2(self.lw / 2, self.lh / 2)
        self.card = PlaceholderCard(self.center)

    def update(self, dt):
        self.card.state.is_hovered = True
        self.card.state._last_frame_hovered = True
        self.card.update(dt)

    def render(self, logical_texture):
        self.card.render(logical_texture)
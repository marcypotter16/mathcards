from typing import TYPE_CHECKING

from pyray import RenderTexture

from entities.card.op_card import OpCard, OperatorType
from entities.card.placeholder import PlaceholderCard
from entities.game_manager.dataclasses import GameView
from entities.game_manager.manager import MatchManager
from entities.renderer import GameViewRenderer
if TYPE_CHECKING:
    from state_manager import StateManager
from mathematics.vector import Vector2
from serialization_test import make_game_state
from states.base import State


class TestState(State):
    def __init__(self, game: StateManager, data=None) -> None:
        super().__init__(game, data)
        gs = make_game_state(game)
        gss = gs.serialize()
        viewer = "p1" # p2
        gw = GameView.to_view(gss, viewer)
        gwr = GameViewRenderer(gw, game, gs.cards)
        self.var = MatchManager(game, gs, gwr)
        # self.var = PlaceholderCard(Vector2(500, 500))


    def update(self, dt: float) -> None:
        self.var.update(dt)

    def render(self, logical_texture: RenderTexture | None = None) -> None:
        super().render(logical_texture)
        self.var.render(logical_texture)

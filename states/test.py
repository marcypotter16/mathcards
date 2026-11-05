from typing import TYPE_CHECKING

from pyray import RenderTexture

from entities.card.op_card import OpCard, OperatorType
from entities.card.placeholder import PlaceholderCard
from entities.game_manager.dataclasses import GameView
from entities.renderer import GameViewRenderer
if TYPE_CHECKING:
    from game import Game
from mathematics.vector import Vector2
from serialization_test import make_game_state
from states.base import State


class TestState(State):
    def __init__(self, game: Game, data=None) -> None:
        super().__init__(game, data)
        gs = make_game_state()
        gss = gs.serialize()
        viewer = "p1" # p2
        gw = GameView.to_view(gss, viewer)
        self.var = GameViewRenderer(gw, gs.cards)
        # self.var = PlaceholderCard(Vector2(500, 500))


    def update(self, dt: float) -> None:
        self.var.update(dt)

    def render(self, logical_texture: RenderTexture | None = None) -> None:
        super().render(logical_texture)
        self.var.render(logical_texture)


def spawn_operators(game) -> list[OpCard]:
    cards = []
    for i, t in enumerate(OperatorType):
        c = OpCard(t, game.tfr)
        c.place_card(Vector2(400 + (c.DIMENSIONS.x + 10) * i, 400))
        cards.append(c)
    return cards
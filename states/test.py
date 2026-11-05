from pyray import RenderTexture

from Settings import WINDOW
from entities.board import Board
from entities.card.eor_card import EORCard
from entities.card.op_card import OpCard
from entities.game_manager.dataclasses import OperatorType
from entities.slot import Slot
from game import Game
from mathematics.poly import Polynomial
from mathematics.ring import QQ, ZZ, Frac, PolyRing, ZZn
from mathematics.vector import Vector2
from states.base import State


class TestState(State):
    def __init__(self, game: Game, data=None) -> None:
        super().__init__(game, data)
        # self.card = EORCard(ZZn(6), 12, game.tfr)
        self.center = Vector2(WINDOW["L_WIDTH"] / 2, WINDOW["L_HEIGHT"] / 2)
        self.var = Board(game.tfr)
        self.var.place_center(self.center)
        for i in range(2):
            for j in range(3):
                self.var.slotgrid[(i, j)].put_card(OpCard(OperatorType.INVERT, game.tfr))
        ser = self.var.serialize()
        print(ser, "\n", self.var.deserialize(ser, game.tfr))


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
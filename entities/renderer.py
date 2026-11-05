from Settings import WINDOW
from entities.base import Entity
from entities.card.base import BaseCard, CardId, CardSer
from entities.game_manager.dataclasses import GameView

import pyray as rl

from entities.hand_manager import HandManager
from mathematics.vector import Vector2


class GameViewRenderer(Entity):
    def __init__(self, gw: GameView, cards: dict[CardId, BaseCard]) -> None:
        print(gw)
        self.gw = gw
        self.lh, self.lw = WINDOW["L_HEIGHT"], WINDOW["L_WIDTH"]
        self.me = gw.me
        self.op = [pid for pid in gw.players.keys() if pid != self.me][0]

        self.my_hand_center = Vector2(self.lw / 2, self.lh - 100)
        self.opp_hand_center = Vector2(self.lw / 2, 100)

        self.my_hand_manager = HandManager(self.my_hand_center, self.gw.players[self.me], cards)
        self.opp_hand_manager = HandManager(self.opp_hand_center, self.gw.players[self.op], cards)

    def update(self, dt: float):
        self.my_hand_manager.update(dt)
        self.opp_hand_manager.update(dt)

    def render(self, logical_texture: rl.RenderTexture | None = None) -> None:
        self.my_hand_manager.render(logical_texture)
        self.opp_hand_manager.render(logical_texture)
import pyray as rl

from entities.card.base import BaseCard
from entities.game_manager.actions import CardEndedDragging, OpCardStartResolving
from entities.game_manager.events import EVENT_BUS
from entities.player import PlayerId
from entities.printer import Printer
from interfaces import DropResult, DropZone
from mathematics.vector import Vector2


class OpSpellDrop(DropZone):
    def __init__(self, rect: rl.Rectangle, resolving_card_center: Vector2, player_id: PlayerId):
        self.rect = rect
        self.resolving_card_center = resolving_card_center
        self.player_id = player_id
        self.is_visible = False
        self.resolving_card: BaseCard | None = None

    def try_accept_drop(self, act: CardEndedDragging) -> DropResult:
        if not self.is_visible:
            return DropResult.Outside

        inside = rl.check_collision_point_rec(act.position.raylib_ref, self.rect)
        if not inside:
            self.is_visible = False
            self.resolving_card = None
            return DropResult.Outside

        c = act.card
        if not c.is_playable:
            Printer.print("Can't play a non playable card")
            self.is_visible = False
            return DropResult.InsideInvalid

        # assert type(c) in {OperatorCard, SpellCard}

        # # Handle the visual tween & own state
        # self.resolving_card = c
        # self.resolving_card.tween_scale(1.5)
        # self.resolving_card.tween_center(self.resolving_card_center, 0.4,
        #                                  callback=setattr(self.resolving_card.state, "is_hovered", False))
        # # self.resolving_card.state.is_hovered = False
        # #, callback=setattr(c.state, "is_hovered", False)
        # self.is_visible = False

        # # Notify the game controller to switch state to SELECT_BOARD_CARDS
        EVENT_BUS.emit(OpCardStartResolving(self.player_id, c.card_id))
        return DropResult.Accepted

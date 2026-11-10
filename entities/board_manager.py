from typing import Any

from pyray import RenderTexture

from entities.base import Entity
from entities.card.base import BaseCard
from entities.card.factory import card_from_ser
from entities.card.base import CardId
from entities.game_manager.actions import CardEndedDragging, CardShouldSnapBack, PlayCardToSlotAction
from entities.game_manager.events import EVENT_BUS
from entities.player import PlayerId, PlayerView
from entities.slot import Slot
from mathematics.vector import Vector2
from entities.printer import Printer

import pyray as rl

class BoardManager(Entity):
    """It's a 3col x 2row grid of Slots"""
    NCOL = 6
    NROW = 1
    MARGIN = 10
    SLOT_DIM = Slot.DIMENSIONS + Vector2(Slot.PADDING * 2, Slot.PADDING * 2)

    def __init__(self, center: Vector2, cards: dict[CardId, BaseCard], pw: PlayerView, me: PlayerId) -> None:
        super().__init__()
        self.slotgrid: dict[tuple[int, int], Slot] = {}

        self.pw = pw
        self.me = me
        self.is_mine = pw.viewer == self.me
        self.center = center
        self.cards = cards
        EVENT_BUS.subscribe(CardEndedDragging, self._handle_card_ended_drag)
        self._fill_grid()

        # self.glow_slots = False

    @property
    def width(self) -> float:
        return (self.NCOL * self.SLOT_DIM.x) + ((self.NCOL - 1) * self.MARGIN)
    
    @property
    def height(self) -> float:
        return (self.NROW * self.SLOT_DIM.y) + ((self.NROW - 1) * self.MARGIN)
    
    @property
    def topleft(self) -> Vector2:
        return self.center - Vector2(self.width, self.height) * .5

    def place_center(self, new_center: Vector2):
        offset = new_center - self.center
        self.center = new_center
        for slot in self.slotgrid.values():
            slot.place_center(slot.center + offset)

    def sync(self, board_view: dict[str, CardId | None], cards: dict[CardId, BaseCard]):
        for key, cid in board_view.items():
            row, col = map(int, key.split(","))
            slot = self.slotgrid[(row, col)]
            
            if cid is not None:
                # If the slot is empty but the state says there's a card, animate it in
                if slot.content is None or slot.content.card_id != cid:
                    card = cards[cid]
                    slot.put_card(card) # This tweens the card to the slot center!
            else:
                # State says empty, so clear it (but render leaving cards!)
                if slot.content is not None and slot.content.state.leaving_to_gy:
                    continue
                slot.content = None

    def _fill_grid(self):
        for row in range(self.NROW):
            for col in range(self.NCOL):
                s = Slot()
                
                # Calculate exact position: 
                # (Slot width * column) + (Margin * column)
                x = self.topleft.x + col * (self.SLOT_DIM.x + self.MARGIN)
                y = self.topleft.y + row * (self.SLOT_DIM.y + self.MARGIN)
                
                s.place_topleft(Vector2(x, y))
                self.slotgrid[(row, col)] = s

    def _handle_card_ended_drag(self, act: CardEndedDragging):
        if not self.is_mine:
            return
        
        pos = act.position
        for coord, slot in self.slotgrid.items():
            if rl.check_collision_point_rec(pos.raylib_ref, slot.rec):
                if slot.is_free():
                    EVENT_BUS.emit(PlayCardToSlotAction(self.pw.viewer, act.card_id, coord))
                    return
                else:
                    EVENT_BUS.emit(CardShouldSnapBack(self.cards[act.card_id], reason="Slot occupied"))
                    return
        else:
            print("\n", pos, self.center, "\n")
            EVENT_BUS.emit(CardShouldSnapBack(self.cards[act.card_id], reason="Dropped outside of board"))

    def update(self, dt: float) -> None:
        for slot in self.slotgrid.values():
            slot.update(dt)
        # mp = rl.get_mouse_position()
        # Printer.print(mp.x, mp.y)

    def render(self, logical_texture: RenderTexture | None) -> None:
        for slot in self.slotgrid.values():
            slot.render(logical_texture)
        # rl.draw_rectangle(int(self.topleft.x), int(self.topleft.y), int(self.width), int(self.height), rl.GREEN)
        # rl.draw_circle(int(self.center.x), int(self.center.y), 5, rl.RED)

    
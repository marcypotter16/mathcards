from typing import Any

from pyray import RenderTexture

from entities.base import Entity
from entities.card.base import BaseCard
from entities.card.factory import card_from_ser
from entities.card.base import CardId, CardSer, ElementCardSer
from entities.slot import Slot
from mathematics.vector import Vector2

import pyray as rl

class Board(Entity):
    """It's a 3col x 2row grid of Slots"""
    NCOL = 3
    NROW = 2
    MARGIN = 10
    SLOT_DIM = Slot.DIMENSIONS + Vector2(Slot.PADDING * 2, Slot.PADDING * 2)

    def __init__(self) -> None:
        super().__init__()
        self.slotgrid: dict[tuple[int, int], Slot] = {}

        self.center = Vector2(400, 400)
        self._fill_grid()

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

    def __repr__(self) -> str:
        # Each cell is a fixed-width 3-char token so columns line up regardless of content.
        def token(slot: Slot) -> str:
            if slot.content is None:
                return " . "
            # return f" {slot.content} "   # see glyph() below
            return " x "

        lines = [f"Board {self.NROW}x{self.NCOL}"]
        # column header
        header = "    " + " ".join(f"{j:>3}" for j in range(self.NCOL))
        lines.append(header)
        for i in range(self.NROW):
            row = " ".join(token(self.slotgrid[(i, j)]) for j in range(self.NCOL))
            lines.append(f"{i:>3} {row}")
        return "\n".join(lines)

    def update(self, dt: float) -> None:
        for slot in self.slotgrid.values():
            slot.update(dt)

    def render(self, logical_texture: RenderTexture | None) -> None:
        for slot in self.slotgrid.values():
            slot.render(logical_texture)
        # rl.draw_rectangle(int(self.topleft.x), int(self.topleft.y), int(self.width), int(self.height), rl.GREEN)
        # rl.draw_circle(int(self.center.x), int(self.center.y), 5, rl.RED)


    ### SERIALIZATION ###

    def serialize(self) -> dict[str, CardId | None]:
        return {
            self._cell_key(coord[0], coord[1]): slot.content.card_id if slot.content else None 
            for coord, slot in self.slotgrid.items()
        }

    @staticmethod
    def _cell_key(i: int, j: int) -> str:
        return f"{i},{j}"

    def apply(self, sd: dict[str, CardId | None], cards: dict[CardId, BaseCard]) -> None:
        seen: set[tuple[int, int]] = set()
        for key, new_cid in sd.items():
            i, j = (int(x) for x in key.split(","))
            coords = (i, j)
            seen.add(coords)
            slot = self.slotgrid[coords]

            current_cid = slot.content.card_id if slot.content is not None else None
            if new_cid == current_cid:
                continue

            if new_cid is None:
                slot.content = None
                continue

            if new_cid not in cards:
                raise ValueError(f"Board.apply: unknown card id {new_cid}")
            slot.content = cards[new_cid]         # replace, don't apply

        for coords, slot in self.slotgrid.items():
            if coords not in seen:
                slot.content = None

    # @staticmethod
    # def _same_card(card: BaseCard, ser: CardId) -> bool:
    #     return type(card.serialize()) is type(ser) and card.card_id == ser.id

    @classmethod
    def deserialize(cls, bss: dict[str, CardId | None], cards: dict[CardId, BaseCard]) -> 'Board':
        board = cls()
        # optional: validate every cid exists in `cards`
        for key, cid in bss.items():
            if cid is not None:
                if cid not in cards:
                    raise ValueError(f"Board.deserialize: unknown card id {cid}")
                i, j = (int(x) for x in key.split(","))
                board.slotgrid[(i, j)].put_card(cards[cid])
        return board
        
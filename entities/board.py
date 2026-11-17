

from entities.card.base import CardId


class Board:

    class SlotOccupiedError(IndexError):
        pass

    N_ROWS = 1
    N_COLS = 6

    def __init__(self) -> None:
        self.grid: dict[str, CardId | None] = {}
        for i in range(self.N_ROWS):
            for j in range(self.N_COLS):
                self.grid[f"{i},{j}"] = None

    def insert_card(self, cid: CardId, slot: tuple[int, int]): 
        key = f"{slot[0]},{slot[1]}"
        if self.grid[key] is not None:
            raise self.SlotOccupiedError(f"Trying to insert a card in an occupied slot {slot}")
        self.grid[key] = cid

    @property
    def is_full(self) -> bool:
        return all(c is not None for c in self.grid.values())

    def serialize(self) -> dict[str, CardId | None]:
        return self.grid

    @classmethod
    def deserialize(cls, d: dict[str, CardId | None]):
        b = cls()
        b.grid = d
        return b
        
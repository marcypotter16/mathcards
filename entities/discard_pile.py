from dataclasses import dataclass
from typing import Sequence

from entities.card.base import CardId

@dataclass
class DiscardPile(Sequence):
    cards: list[CardId]

    def serialize(self):
        return self.cards

    @classmethod
    def deserialize(cls, c: list[CardId]):
        dp = cls([])
        dp.cards = c
        return dp

    def __len__(self) -> int:
        return len(self.cards)

    def __getitem__(self, index: slice[int | None, int | None, int | None]) -> Sequence:
        return self.cards[index]
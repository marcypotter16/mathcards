from entities.base import Entity
from entities.card.base import BaseCard, CardId


class Deck(Entity):
    def __init__(self) -> None:
        super().__init__()
        self.cards: list[CardId] = []

    def serialize(self) -> list[CardId]:
        return self.cards

    @classmethod
    def deserialize(cls, ds: list[CardId]):
        d = cls()
        d.cards = ds
        return d

    
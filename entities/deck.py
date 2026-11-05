from entities.base import Entity
from entities.card.base import BaseCard, CardId


class Deck(Entity):
    def __init__(self) -> None:
        super().__init__()
        self.cards: list[BaseCard] = []

    def serialize(self) -> list[CardId]:
        return [card.card_id for card in self.cards]

    @classmethod
    def deserialize(cls, ds: list[CardId], cards: dict[CardId, BaseCard]):
        d = cls()
        d.cards = [cards[cid] for cid in ds]
        return d

    
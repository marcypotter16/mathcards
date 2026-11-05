

from entities.card.base import CardId


class Hand:
    def __init__(self) -> None:
        super().__init__()
        self.cards: list[CardId] = []

    def insert_card(self, card_id: CardId, index: int = -1):
        self.cards.insert(index, card_id)
    
    def serialize(self) -> list[CardId]:
        return self.cards

    @staticmethod
    def deserialize(data: list[CardId]) -> Hand:
        h = Hand()
        h.cards = data
        return h

    def __contains__(self, item: CardId):
        return item in self.cards

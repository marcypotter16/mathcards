from entities.card.base import BaseCard
from entities.card.CardManager import CardManager
from entities.card.base import CardId

class Hand(CardManager):
    def __init__(self) -> None:
        super().__init__()

    def insert_card(self, c: BaseCard, index: int):
        # If it's already managed, pull it out so we can reposition it
        if c in self.cards:
            self.cards.remove(c)
        
        # Insert cleanly at the desired index (shifts everything else automatically)
        self.cards.insert(index, c)
        
        # Re-sync all z_indices to match their exact position in the hand list
        for i, card in enumerate(self.cards):
            card.z_index = i

    def serialize(self) -> list[CardId]:
        return [card.card_id for card in self.cards]

    @staticmethod
    def deserialize(data: list[CardId], cards: dict[CardId, BaseCard]) -> Hand:
        h = Hand()
        h.cards = [cards[cid] for cid in data]
        for i, card in enumerate(h.cards):
            card.z_index = i
        return h
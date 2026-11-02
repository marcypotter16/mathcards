from entities.card.Card import BaseCard
from entities.card.CardManager import CardManager


class HandManager(CardManager):
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
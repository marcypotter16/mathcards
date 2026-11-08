from entities.card.base import BaseCard, CardId


class Deck:
    def __init__(self) -> None:
        self.cards: list[CardId] = []

    @property
    def size(self) -> int:
        return len(self.cards)

    def can_draw(self, amount: int = 1) -> bool:
        return amount <= len(self.cards)

    def draw_cards(self, amount: int = 1) -> list[CardId]:
        if not self.can_draw(amount):
            raise IndexError("Trying to draw more cards then cards in deck.")
        print(f"Drawing {amount} cards from {self}")
        l = []
        for _ in range(amount):
            l.append(self.cards.pop())
        return l

    def serialize(self) -> list[CardId]:
        return self.cards

    @classmethod
    def deserialize(cls, ds: list[CardId]):
        d = cls()
        d.cards = ds
        return d

    
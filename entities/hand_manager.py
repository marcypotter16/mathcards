from entities.card.CardManager import CardManager
from entities.card.base import BaseCard, CardId
from entities.card.placeholder import PlaceholderCard
from entities.game_manager.dataclasses import PlayerView
from mathematics.vector import Vector2


class HandManager(CardManager):
    def __init__(self, center: Vector2, player_view: PlayerView, cards: dict[CardId, BaseCard]) -> None:
        super().__init__()
        self.center = center
        self.pw = player_view
        hand = self.pw.hand
        self.margin = 10
        self.distance = 100
        n = self.pw.hand_size
        total_width = (n - 1) * self.distance
        start_x = self.center.x - (total_width / 2)

        for i in range(n):
            x = start_x + (i * self.distance)
            pos = Vector2(x, self.center.y)
            
            if hand is None:
                c = PlaceholderCard(pos)
            else:
                c = cards[hand[i]]
                c.place_card(pos)
                
            self.spawn_card(c, i)

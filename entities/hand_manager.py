from Settings import WINDOW
from entities.card.CardManager import CardManager
from entities.card.base import BaseCard, CardId
from entities.card.placeholder import PlaceholderCard
from entities.game_manager.actions import CardInserted, CardShouldSnapBack, PlayCardToSlotAction
from entities.game_manager.dataclasses import PlayerView
from entities.game_manager.events import EVENT_BUS
from entities.player import PlayerId
from mathematics.vector import Vector2

class HandManager(CardManager):
    def __init__(self, center: Vector2, player_view: PlayerView, me: PlayerId, cards: dict[CardId, BaseCard]) -> None:
        super().__init__()
        self.center = center
        self.pw = player_view
        self.me = me
        hand = self.pw.hand
        self.margin = 10
        self.distance = 100
        self.all_cards = cards
        n = self.pw.hand_size
        total_width = (n - 1) * self.distance
        start_x = self.center.x - (total_width / 2)

        # Subscribe to the event!
        EVENT_BUS.subscribe(CardInserted, self._handle_card_inserted_action)
        EVENT_BUS.subscribe(CardShouldSnapBack, self._handle_card_snap_back)
        EVENT_BUS.subscribe(PlayCardToSlotAction, lambda act: self._undrag_card())

        for i in range(n):
            x = start_x + (i * self.distance)
            pos = Vector2(x, self.center.y)
            
            if hand is None:
                c = PlaceholderCard(pos)
            else:
                c = cards[hand[i]]
                c.place_card(pos)
                
            self.spawn_card(c, i)

    def sync(self, new_pw: PlayerView):
        print(f"\nSYNCING VIEW IN HAND MANAGER {new_pw}")
        if new_pw == self.pw:
            return
        
        self.pw = new_pw
        
        if self.pw.hand is not None:
            # 1. For MY hand: Only remove cards that were played.
            # Do NOT rebuild the list, or it will flash.
            self.cards = [c for c in self.cards 
                          if c.card_id in self.pw.hand or c.state.leaving_to_gy
                          ]
        else:
            # 2. For OPPONENT's hand: Match the placeholder count.
            # Add new placeholders off-screen so they fly in.
            while len(self.cards) < self.pw.hand_size:
                c = PlaceholderCard(Vector2(-200, self.center.y))
                self.spawn_card(c, len(self.cards))
            # Remove extra placeholders (if opponent played a card)
            while len(self.cards) > self.pw.hand_size:
                self.cards.pop()

        # 3. Recalculate the fan layout for whatever cards remain
        print(f"CALLING RELAYOUT...\n")
        self._relayout()

    def _relayout(self):
        visible = [c for c in self.cards if not c.state.leaving_to_gy]
        n = len(visible)
        if n == 0:
            return

        total_width = (n - 1) * self.distance
        start_x = self.center.x - (total_width / 2)

        for i, card in enumerate(visible):
            x = start_x + (i * self.distance)
            target_pos = Vector2(x, self.center.y)
            card.center_rest = target_pos
            card.center_before_drag = target_pos
            card.tween_center(target_pos, dur=0.4)

    def _handle_card_inserted_action(self, act: CardInserted):
        # THE FIX: Only animate if I am the one drawing!
        print(f"ACTOR: {act.actor}, VIEWER: {self.pw.viewer}")
        if act.actor != self.pw.viewer:
            return

        if self.pw.hand is not None:
            c = self.all_cards[act.card_id]
            c.place_card(Vector2(200, self.center.y)) 
        else:
            c = PlaceholderCard(Vector2(-200, self.center.y))

        self.spawn_card(c, len(self.cards))
        # self._relayout()

    def _undrag_card(self):
        self._dragged_card = None

    def _handle_card_snap_back(self, act: CardShouldSnapBack):
        act.card.snap_back()
        self.undo_card_above_others(act.card)
        self._dragged_card = None
        act.card.state.ended_dragging = True

    def update(self, dt: float):
        if self.pw.viewer != self.me:
            return

        # Drop finished leavers without waiting for the next sync.
        self.cards = [
            c for c in self.cards
            if c.state.leaving_to_gy or (self.pw.hand is not None and c.card_id in self.pw.hand)
            or (self.pw.hand is None and isinstance(c, PlaceholderCard))
        ]
        super().update(dt)
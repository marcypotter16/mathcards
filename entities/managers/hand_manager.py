from draw_debug import draw_debug
from entities.card.base import BaseCard, CardId
from entities.card.CardManager import CardManager
from entities.card.eor_card import RingElementCard
from entities.card.op_card import OperatorCard, OperatorType
from entities.card.placeholder import PlaceholderCard
from entities.game_manager.actions import (
    CardEndedDragging,
    CardInserted,
    CardShouldSnapBack,
    CardToDiscardPileAction,
    PlayCardToSlotAction,
)
from entities.game_manager.dataclasses import GameView, PlayerView
from entities.game_manager.events import EVENT_BUS
from entities.player import PlayerId
from mathematics.base import Category
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
        EVENT_BUS.subscribe(CardToDiscardPileAction, self._handle_card_discarded)
        EVENT_BUS.subscribe(PlayCardToSlotAction, lambda act: self._undrag_card())
        EVENT_BUS.subscribe(CardEndedDragging, lambda act: self._undrag_card())

        for i in range(n):
            x = start_x + (i * self.distance)
            pos = Vector2(x, self.center.y)
            
            if hand is None:
                c = PlaceholderCard(pos)
            else:
                c = cards[hand[i]]
                c.place_card(pos)
                
            self.spawn_card(c, i)

    def sync(self, new_gw: GameView):
        # print(f"\nSYNCING VIEW IN HAND MANAGER {new_pw}")
        new_pw = new_gw.players[self.me]
        view_changed = new_pw != self.pw
        old_cards = [self._debug_card(c) for c in self.cards]
        self.pw = new_pw

        if self.pw.hand is not None:
            # 1. For MY hand: Only remove cards that were played.
            if view_changed:
                self.cards = [
                                c for c in self.cards
                                if c.card_id in self.pw.hand or c.state.leaving_to_gy
                            ]
            for c in self.cards:
                if isinstance(c, OperatorCard):
                    if new_gw.active_category == Category.AbGp and c.op_type in { OperatorType.MUL, OperatorType.INVERT }:
                        c.is_playable = False
                        continue
                    c.is_playable = True
                elif isinstance(c, RingElementCard):
                    if new_gw.players[self.me].board.is_full:
                        c.is_playable = False
                        continue
                    if new_gw.active_ring != c.ring:
                        c.is_playable = False
                        continue
                    c.is_playable = True
        elif view_changed:
            # 2. For OPPONENT's hand: Match the placeholder count.
            # Add new placeholders off-screen so they fly in.
            while len(self.cards) < self.pw.hand_size:
                c = PlaceholderCard(Vector2(-200, self.center.y))
                self.spawn_card(c, len(self.cards))
            # Remove extra placeholders (if opponent played a card)
            while len(self.cards) > self.pw.hand_size:
                self.cards.pop()

        if view_changed:
            # 3. Recalculate the fan layout for whatever cards remain
            # print(f"CALLING RELAYOUT...\n")
            self._relayout()
            draw_debug(
                "HandManager.sync",
                f"manager={id(self)} viewer={self.pw.viewer} owner={self.me}",
                f"hand={self.pw.hand}",
                f"cards_before={old_cards}",
                f"cards_after={[self._debug_card(c) for c in self.cards]}",
            )

    @staticmethod
    def _debug_card(card):
        if isinstance(card, PlaceholderCard):
            return f"placeholder@{card.center}"
        return f"{type(card).__name__}#{card.card_id}@{card.center}"

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
        before = [self._debug_card(c) for c in self.cards]
        draw_debug(
            "CardInserted handler",
            f"manager={id(self)} viewer={self.pw.viewer} owner={self.me}",
            f"actor={act.actor} card={act.card_id} visible_hand={self.pw.hand is not None}",
            f"cards_before={before}",
        )
        if act.actor != self.pw.viewer:
            draw_debug("CardInserted ignored: actor differs from viewer")
            return

        if self.pw.hand is not None:
            c = self.all_cards[act.card_id]
            c.place_card(Vector2(200, self.center.y)) 
        else:
            c = PlaceholderCard(Vector2(-200, self.center.y))

        self.spawn_card(c, len(self.cards))
        draw_debug(
            "CardInserted spawned",
            f"manager={id(self)} card={self._debug_card(c)}",
            f"cards_after={[self._debug_card(card) for card in self.cards]}",
        )
        # self._relayout()

    def _undrag_card(self):
        self._dragged_card = None

    def _handle_card_discarded(self, act: CardToDiscardPileAction):
        # Operator and spell cards stay in the hand while their target selection
        # is open. Clear the held-card reference only once the played card leaves.
        card = self.all_cards.get(act.card_id)
        if card is not None:
            card.state.hover_locked = False
        if self._dragged_card is not None and self._dragged_card.card_id == act.card_id:
            self._dragged_card.state.is_dragged = False
            self._dragged_card.state._last_frame_dragged = False
            self._dragged_card = None

    def _handle_card_snap_back(self, act: CardShouldSnapBack):
        # owns_card = act.card in self.cards
        # print(
        #     f"[DND] snap-back event manager={id(self)} owner={self.me} "
        #     f"card={type(act.card).__name__}#{act.card.card_id} owns={owns_card} "
        #     f"cached_z={self._cached_hovered_card_z_index} "
        #     f"current_z={act.card.z_index}"
        # )
        act.card.state.hover_locked = False
        act.card.snap_back()
        self.undo_card_above_others(act.card)
        self._dragged_card = None
        act.card.state.ended_dragging = True

    def update(self, dt: float):
        if self.pw.viewer != self.me:
            return
        # print(self._dragged_card)

        # Drop finished leavers without waiting for the next sync.
        self.cards = [
            c for c in self.cards
            if c.state.leaving_to_gy or (self.pw.hand is not None and c.card_id in self.pw.hand)
            or (self.pw.hand is None and isinstance(c, PlaceholderCard))
        ]
        draw_debug(
            "HandManager.update",
            f"manager={id(self)} viewer={self.pw.viewer} owner={self.me}",
            f"hand={self.pw.hand}",
            f"cards={[self._debug_card(c) for c in self.cards]}",
        )
        super().update(dt)

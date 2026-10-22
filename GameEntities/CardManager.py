import pyray as rl

from GameEntities.Card import Card, Suit
from GameEntities.Entity import Entity
from Vector import Vector2


class CardManager(Entity):
    def __init__(self) -> None:
        self.cards:                         dict[int, Card]         = {} # id, card
        self.cards_sorted:                  list[Card]              = []
        self.auto_id:                       int                     = 0
        self._cached_hovered_card_z_index:  int | None              = None
        self._needs_sorting:                bool                    = False
        self._hovered_card:                 Card | None             = None
        self._dragged_card:                 Card | None             = None

    def sort(self):
        self.cards_sorted = sorted(self.cards.values(), key=lambda c: c.z_index)

    def spawn_card(self, c: Card, z_index: int):
        c.z_index = z_index
        self.cards[self.auto_id] = c
        self.sort()
        self.auto_id += 1

    def destroy_card(self, id: int):
        if id in self.cards.keys():
            card = self.cards.pop(id)
            card.unload()
            self.sort()

    def bring_card_above_others(self, c: Card):
        self._cached_hovered_card_z_index = c.z_index
        c.z_index = 100
        self._needs_sorting = True

    def undo_card_above_others(self, card):
        if card is not None and self._cached_hovered_card_z_index is not None:
            card.z_index = self._cached_hovered_card_z_index
            self._cached_hovered_card_z_index = None
            self._needs_sorting = True

    def _test(self):
        for rank in range(1, 11):
            card = Card(rank, Suit.SPADES)
            card.place_card(Vector2(200 + 50 * rank, 400))
            self.spawn_card(card, rank)

    def hover_card(self, card: Card):
        card.state.is_hovered = True
        self._hovered_card = card
        
        if not card.state._last_frame_hovered:
            card.state.started_hovering = True
            print(f"Started hovering: {self._hovered_card}")

    def unload(self):
        for card in self.cards_sorted:
            card.unload()

    def update(self, dt: float):
        self._needs_sorting = False
        mouse_pos = rl.get_mouse_position()
        mouse_down = rl.is_mouse_button_down(rl.MouseButton.MOUSE_BUTTON_LEFT)
        
        # 1. Gather what is hovered *this* frame using your clean list comprehension
        hovered_cards = [c for c in self.cards_sorted if rl.check_collision_point_rec(mouse_pos, c.get_rect())]
        
        current_top_hover = hovered_cards[-1] if hovered_cards else None

        # Iterate backwards (highest z_index / topmost card first)
        for card in reversed(self.cards_sorted):
            # Clear triggers first
            card.state.clear_frame_triggers()

            # Is this specific card the one being hovered this frame?
            is_hovered_this_frame = (card == current_top_hover) or self._dragged_card == card

            # Update the card's native is_hovered state
            card.state.is_hovered = is_hovered_this_frame
            # Check for STARTED hovering transition
            if is_hovered_this_frame and not card.state._last_frame_hovered:
                card.state.started_hovering = True
                self._hovered_card = card
                print(f"Started hovering: {card}")

            # Check for ENDED hovering transition
            elif not is_hovered_this_frame and card.state._last_frame_hovered:
                card.state.ended_hovering = True
                if self._hovered_card == card:
                    self._hovered_card = None
                    self._needs_sorting = True
                print(f"Ended hovering: {card}")

            # Check whether or not the card was hovered this frame or last frame (mouse pos could get out of card's rect if moved quickly)
            if mouse_down and (is_hovered_this_frame or card.state._last_frame_dragged):
                if self._dragged_card is None:
                    card.state.is_dragged = True
                    if not card.state._last_frame_dragged:
                        self._dragged_card = card
                        self.bring_card_above_others(card)
                        card.state.started_dragging = True

            else:
                card.state.is_dragged = False
                if card.state._last_frame_dragged:
                    self.undo_card_above_others(card)
                    self._dragged_card = None
                    card.state.ended_dragging = True

            # 3. Update physics/tweens
            card.update(dt)
            
            # 4. CRITICAL: Update last-frame variables at the very end of this card's frame
            card.state.update_last_frame_vars()

        if self._needs_sorting:
            self.sort()
            self._needs_sorting = False
    
    def render(self, logical_texture: rl.RenderTexture):
        for card in self.cards_sorted:
            card.render(logical_texture)
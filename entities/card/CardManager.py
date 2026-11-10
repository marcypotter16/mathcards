from typing import Sequence

import pyray as rl
from entities.card.base import BaseCard
from entities.base import Entity
from entities.game_manager.actions import CardEndedDragging, CardStartedDragging
from entities.game_manager.events import EVENT_BUS
from mathematics.vector import Vector2

class CardManager(Entity):
    def __init__(self) -> None:
        # Single source of truth: A list maintains both the collection AND the order/z_index!
        self.cards: list[BaseCard] = []
        
        self._cached_hovered_card_z_index: int | None = None
        self._needs_sorting: bool = False
        self._hovered_card: BaseCard | None = None
        self._dragged_card: BaseCard | None = None

    def sort_by_z_index(self):
        """Sorts the cards list based on their z_index attribute."""
        self.cards.sort(key=lambda c: c.z_index)

    def spawn_card(self, c: BaseCard, z_index: int):
        c.z_index = z_index
        self.cards.append(c)
        self.sort_by_z_index()

    def destroy_card(self, card: BaseCard):
        """Destroy by card reference directly, avoiding brittle integer IDs."""
        if card in self.cards:
            self.cards.remove(card)
            card.unload()

    def bring_card_above_others(self, c: BaseCard):
        self._cached_hovered_card_z_index = c.z_index
        c.z_index = 100
        self._needs_sorting = True

    def undo_card_above_others(self, card):
        if card is not None and self._cached_hovered_card_z_index is not None:
            card.z_index = self._cached_hovered_card_z_index
            self._cached_hovered_card_z_index = None
            self._needs_sorting = True

    def unload(self):
        for card in self.cards:
            card.unload()

    def update(self, dt: float):
        self._needs_sorting = False
        mouse_pos = rl.get_mouse_position()
        mouse_down = rl.is_mouse_button_down(rl.MouseButton.MOUSE_BUTTON_LEFT)
        
        # Since self.cards is always sorted by z_index, index -1 is the topmost drawn card
        hovered_cards = [c for c in self.cards if rl.check_collision_point_rec(mouse_pos, c.get_rect())]
        current_top_hover = hovered_cards[-1] if hovered_cards else None

        for card in reversed(self.cards):
            card.state.clear_frame_triggers()

            if card.state.leaving_to_gy:
                card.update(dt)
                card.state.update_last_frame_vars()
                continue

            is_hovered_this_frame = (card == current_top_hover) or (self._dragged_card == card)

            card.state.is_hovered = is_hovered_this_frame
            if is_hovered_this_frame and not card.state._last_frame_hovered:
                card.state.started_hovering = True
                self._hovered_card = card
                # print(f"Started hovering: {card}")

            elif not is_hovered_this_frame and card.state._last_frame_hovered:
                card.state.ended_hovering = True
                if self._hovered_card == card:
                    self._hovered_card = None
                    self._needs_sorting = True
                # print(f"Ended hovering: {card}")

            if mouse_down and (is_hovered_this_frame or card.state._last_frame_dragged):
                if self._dragged_card is None:
                    card.state.is_dragged = True
                    if not card.state._last_frame_dragged:
                        self._dragged_card = card
                        self.bring_card_above_others(card)
                        card.state.started_dragging = True
                        EVENT_BUS.emit(CardStartedDragging(card))
            else:
                card.state.is_dragged = False
                if card.state._last_frame_dragged:
                    # self.undo_card_above_others(card)
                    # self._dragged_card = None
                    # card.state.ended_dragging = True
                    EVENT_BUS.emit(CardEndedDragging(card.card_id, card.center))

            card.update(dt)
            card.state.update_last_frame_vars()

        if self._needs_sorting:
            self.sort_by_z_index()
            self._needs_sorting = False
    
    def render(self, logical_texture: rl.RenderTexture | None = None):
        for card in self.cards:
            card.render(logical_texture)
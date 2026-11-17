from entities.card.eor_card import RingElementCard
from entities.game_manager.actions import *
from entities.game_manager.dataclasses import GameState, GameView
from entities.game_manager.events import EVENT_BUS
from entities.printer import Printer
from entities.renderer import GameViewRenderer
from mathematics.canonical_maps import Conversion
from state_manager import StateManager
from states.discard_pile import DiscardPileDetailState


class MatchManager:
    def __init__(self, sm: StateManager, gs: GameState, renderer: GameViewRenderer):
        self.gs = gs
        self.sm = sm
        self.renderer = renderer
        self.me = renderer.me
        self.event_bus = EVENT_BUS
        self.event_bus.subscribe(DrawCardAction, self.request_action)
        self.event_bus.subscribe(PlayCardToSlotAction, self.request_action)
        self.event_bus.subscribe(StartTurnAction, self.request_action)
        self.event_bus.subscribe(PlayOpCardAction, self.request_action)
        self.event_bus.subscribe(PlaySpellCardAction, self.request_action)
        self.event_bus.subscribe(DiscardPileOpenDetail, lambda a: self.sm.enter_state(DiscardPileDetailState(self.sm, a.discard_pile, gs.cards)))
        self.event_bus.subscribe(CardToDiscardPileAction, self._handle_card_to_gy)
        self.event_bus.subscribe(ChangeRingAction, self.request_action)

        # Run the same view reconciliation used after actions so card playability
        # reflects the initial category before the first player action.
        self.renderer.sync(GameView.to_view(self.gs.serialize(), self.me))

    def _handle_card_to_gy(self, action: CardToDiscardPileAction):
        c = self.gs.cards[action.card_id]
        c.state.leaving_to_gy = True
        def _done():
            c.state.leaving_to_gy = False
            # Drop the card out of any board slot still showing it
            for board in self.renderer.boards.values():
                for slot in board.slotgrid.values():
                    if slot.content is c:
                        slot.content = None
        c.tween_center(
            self.renderer.dps[action.player_id].center,
            dur=0.4,
            callback=_done,
        )
        c.tween_scale(1.0)

    def request_action(self, action: GameAction) -> None:
        """Called by the UI (e.g. DeckManager) when the player wants to do something."""
        
        # 1. Local validation (instant feedback)
        ok, reason = action.can_apply(self.gs)
        if not ok:
            Printer.print(f"Action rejected: {reason}")
            if type(action) in { PlayCardToSlotAction, PlayOpCardAction, PlaySpellCardAction, CardRingConverted }:
                EVENT_BUS.emit(CardShouldSnapBack(self.gs.cards[action.card_id], reason)) # type: ignore
            # if type(action) == PlayOpCardAction:
            #     EVENT_BUS.emit(CardSrhouldSnapBack(self))
            return

        # 2. Send to server (if online)
        # self.network.send(action)

        # 3. For local play, apply it and animate immediately
        self._apply_and_animate(action)

        if self.gs.n_actions_left <= 0 and not isinstance(action, EndTurnAction):
            self.request_action(EndTurnAction(action.player_id))

    def receive_action_from_server(self, action: GameAction) -> None:
        """Called by the network loop when an action arrives from the opponent/server."""
        self._apply_and_animate(action)

    def _apply_and_animate(self, action: GameAction) -> None:
        if isinstance(action, CardRingConverted):
            old_card = self.gs.cards[action.card_id]
            assert isinstance(old_card, RingElementCard)
            morphism = Conversion.try_get(old_card.ring, self.gs.active_ring)
            assert morphism is not None
            converted_value = morphism(old_card.current_value)
            self.gs.cards[action.card_id] = RingElementCard(
                self.sm,
                self.gs.active_ring,
                converted_value,
                card_id=action.card_id,
            )
        else:
            action.apply(self.gs)
        self.renderer.sync(GameView.to_view(self.gs.serialize(), action.player_id), action)


    def update(self, dt: float):
        self.renderer.update(dt)


    def render(self, logical_texture):
        self.renderer.render(logical_texture)

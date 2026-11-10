from entities.card.op_card import OpCard
from entities.game_manager.dataclasses import GameState, GameView
from entities.game_manager.actions import *
from entities.game_manager.events import EVENT_BUS
from entities.renderer import GameViewRenderer, StateMachine
from state_manager import StateManager

import pyray as rl

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
        self.event_bus.subscribe(DiscardPileOpenDetail, lambda a: self.sm.enter_state(DiscardPileDetailState(self.sm, a.discard_pile, gs.cards)))
        self.event_bus.subscribe(CardToDiscardPileAction, self._handle_card_to_gy)

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
            print(f"Action rejected: {reason}")
            if type(action) in { PlayCardToSlotAction, PlayOpCardAction }:
                EVENT_BUS.emit(CardShouldSnapBack(self.gs.cards[action.card_id], reason)) # type: ignore
            # if type(action) == PlayOpCardAction:
            #     EVENT_BUS.emit(CardShouldSnapBack(self))
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
        action.apply(self.gs)
        self.renderer.sync(GameView.to_view(self.gs.serialize(), action.player_id), action)


    def update(self, dt: float):
        self.renderer.update(dt)


    def render(self, logical_texture):
        self.renderer.render(logical_texture)
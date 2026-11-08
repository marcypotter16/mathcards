from entities.game_manager.dataclasses import GameState, GameView
from entities.game_manager.actions import CardEndedDraggingAction, GameAction, DrawCardAction, PlayCardAction
from entities.game_manager.events import EVENT_BUS
from entities.renderer import GameViewRenderer
from state_manager import StateManager

import pyray as rl

class MatchManager:
    def __init__(self, gs: GameState, renderer: GameViewRenderer):
        self.gs = gs
        self.renderer = renderer
        self.me = renderer.me
        self.event_bus = EVENT_BUS
        self.event_bus.subscribe(DrawCardAction, lambda act: self.request_action(act))
        self.event_bus.subscribe(PlayCardAction, lambda act: self.request_action(act))
        # self.event_bus.subscribe(CardEndedDraggingAction, lambda act: self._handle_card_drop(act))

    def request_action(self, action: GameAction) -> None:
        """Called by the UI (e.g. DeckManager) when the player wants to do something."""
        
        # 1. Local validation (instant feedback)
        ok, reason = action.can_apply(self.gs)
        if not ok:
            print(f"Action rejected: {reason}")
            return

        # 2. Send to server (if online)
        # self.network.send(action)

        # 3. For local play, apply it and animate immediately
        self._apply_and_animate(action)

    def receive_action_from_server(self, action: GameAction) -> None:
        """Called by the network loop when an action arrives from the opponent/server."""
        self._apply_and_animate(action)

    def _apply_and_animate(self, action: GameAction) -> None:
        action.apply(self.gs)
        self.renderer.sync(GameView.to_view(self.gs.serialize(), action.player_id), action)

    # def _handle_card_drop(self, act: CardEndedDraggingAction):
    #     mp = rl.get_mouse_position()
    #     for coord, slot in self.renderer.boards[self.me].slotgrid.items():
    #         if rl.check_collision_point_rec(mp, slot.rec):
    #             EVENT_BUS.emit(PlayCardAction(self.me, act.card_id, coord))

    def update(self, dt: float):
        self.renderer.update(dt)


    def render(self, logical_texture):
        self.renderer.render(logical_texture)
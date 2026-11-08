from Settings import WINDOW
from entities.base import Entity
from entities.board_manager import BoardManager
from entities.card.base import BaseCard, CardId
from entities.deck_manager import DeckManager
from entities.hand_manager import HandManager
from entities.game_manager.dataclasses import GameView
from entities.game_manager.actions import GameAction
from entities.player import PlayerId
from state_manager import StateManager
from mathematics.vector import Vector2
import pyray as rl


class GameViewRenderer(Entity):
    def __init__(self, gw: GameView, sm: StateManager, cards: dict[CardId, BaseCard]) -> None:
        self.gw = gw
        self.lh, self.lw = WINDOW["L_HEIGHT"], WINDOW["L_WIDTH"]
        self.me = gw.me
        self.cards = cards
        
        # Dictionaries to hold managers for ALL players
        self.hands:     dict[PlayerId, HandManager]     = {}
        self.decks:     dict[PlayerId, DeckManager]     = {}
        self.boards:    dict[PlayerId, BoardManager]    = {}

        # Define fixed positions (you can make this dynamic later based on player count)
        my_hand_center      = Vector2(self.lw / 2, self.lh - 120)
        my_deck_center      = Vector2(1700, 900)
        my_board_center     = Vector2(self.lw / 2, self.lh - 320)
        
        opp_hand_center     = Vector2(self.lw / 2, 50)
        opp_deck_center     = Vector2(1700, 200)
        opp_board_center    = Vector2(self.lw / 2, 320)
        
        for pid, pview in gw.players.items():
            if pid == self.me:
                # Me
                self.hands[pid]  = HandManager(my_hand_center, pview, cards)
                self.decks[pid]  = DeckManager(my_deck_center, sm, pview)
                self.boards[pid] = BoardManager(my_board_center, cards, pview, gw.me)
            else:
                # Opponent(s)
                self.hands[pid]  = HandManager(opp_hand_center, pview, cards)
                self.decks[pid]  = DeckManager(opp_deck_center, sm, pview)
                self.boards[pid] = BoardManager(opp_board_center, cards, pview, gw.me)

    def sync(self, gw: GameView, action: GameAction):
        """Called by MatchManager after state changes."""
        self.gw = gw
        
        # Update all managers with the new redacted views
        for pid, pview in gw.players.items():
            self.decks[pid].sync(pview)
            self.boards[pid].sync(pview.board, self.cards)
            if pid == self.me:
                self.hands[pid].sync(pview)
            
            # # # If you want HandManager to animate the new card:
            # if pid == action.player_id:
            #     self.hands[pid].on_action(action, pview)
            # else:
            #     self.hands[pid].sync(pview)

    def update(self, dt: float):
        for hand in self.hands.values():
            hand.update(dt)
        for deck in self.decks.values():
            deck.update(dt)
        for board in self.boards.values():
            board.update(dt)

        if self.hands[self.me]._dragged_card is not None:
            pass

    def render(self, logical_texture: rl.RenderTexture | None = None) -> None:
        for board in self.boards.values():
            board.render(logical_texture)
        for hand in self.hands.values():
            hand.render(logical_texture)
        for deck in self.decks.values():
            deck.render(logical_texture)
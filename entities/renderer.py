from enum import Enum

from Settings import WINDOW
from entities.base import Entity
from entities.board_manager import BoardManager
from entities.card.base import BaseCard, CardId
from entities.card.op_card import OpCard
from entities.deck_manager import DeckManager
from entities.discard_pile_manager import DiscardPileManager
from entities.game_manager.events import EVENT_BUS
from entities.hand_manager import HandManager
from entities.game_manager.dataclasses import GameView
from entities.game_manager.actions import *
from entities.player import PlayerId
from entities.printer import Printer
from entities.ui.button import UIButton
from state_manager import StateManager
from mathematics.vector import Vector2
import pyray as rl

class StateMachine(Enum):
    NORMAL              = 0
    SELECT_BOARD_CARDS  = 1


class GameViewRenderer(Entity):
    def __init__(self, gw: GameView, sm: StateManager, cards: dict[CardId, BaseCard]) -> None:
        self.gw = gw
        self.lh, self.lw = WINDOW["L_HEIGHT"], WINDOW["L_WIDTH"]
        self.me = gw.me
        self.op = [p for p in gw.players if p != self.me][0]
        self.cards = cards
        self.sm = sm

        self.state = StateMachine.NORMAL # STATE MACHINE
        
        # Dictionaries to hold managers for ALL players
        self.hands:     dict[PlayerId, HandManager]         = {}
        self.decks:     dict[PlayerId, DeckManager]         = {}
        self.boards:    dict[PlayerId, BoardManager]        = {}
        self.dps:       dict[PlayerId, DiscardPileManager]  = {}

        # Define fixed positions (you can make this dynamic later based on player count)
        my_hand_center      = Vector2(self.lw / 2, self.lh - 120)
        my_deck_center      = Vector2(1700, 650 + 225 + 20)
        my_board_center     = Vector2(self.lw / 2, self.lh - 320)
        my_dp_center        = Vector2(1700, 650)
        
        opp_hand_center     = Vector2(self.lw / 2, 50)
        opp_deck_center     = Vector2(1700, 150)
        opp_board_center    = Vector2(self.lw / 2, 320)
        opp_dp_center       = Vector2(1700, 150 + 225 + 20)
        
        for pid, pview in gw.players.items():
            if pid == self.me:
                # Me
                self.hands[pid]  = HandManager(my_hand_center, pview, self.me, cards)
                self.decks[pid]  = DeckManager(my_deck_center, sm, pview)
                self.boards[pid] = BoardManager(my_board_center, cards, pview, gw.me)
                self.dps[pid]    = DiscardPileManager(my_dp_center, gw, self.me)
            else:
                # Opponent(s)
                self.hands[pid]  = HandManager(opp_hand_center, pview, self.me, cards)
                self.decks[pid]  = DeckManager(opp_deck_center, sm, pview)
                self.boards[pid] = BoardManager(opp_board_center, cards, pview, gw.me)
                self.dps[pid]    = DiscardPileManager(opp_dp_center, gw, self.op)

        self.op_card_drop_area = rl.Rectangle(
            0.1 * self.lw,
            0.1 * self.lh,
            0.8 * self.lw,
            0.8 * self.lh
        )
        self._show_card_drop_area = False
        EVENT_BUS.subscribe(CardStartedDragging, self._handle_op_card_drag)
        EVENT_BUS.subscribe(CardEndedDragging, self._handle_op_card_drop)

        self.resolving_op_card:     OpCard | None                 = None
        self.resolving_op_center:   Vector2                       = Vector2(200, self.lh / 2)
        self.confirm_btn = UIButton(
            text="Confirm",
            rect=rl.Rectangle(self.lw - 250, self.lh / 2 - 35, 150, 60),
            font=self.sm.font,
            color=rl.GREEN
        )
        self.cancel_btn = UIButton(
            text="Cancel",
            rect=rl.Rectangle(self.lw - 250, self.lh / 2 + 35, 150, 60),
            font=self.sm.font,
            color=rl.RED
        )
    
        self.selected_board_cards:  list[tuple[CardId, PlayerId]] = [] # id, owner (owners should be all the same!!)

    def _handle_op_card_drag(self, a: CardStartedDragging):
        # Printer.print(a.card, type(a.card))
        if type(a.card) == OpCard:
            self._show_card_drop_area = True
            # self.resolving_op_card = a.card

    def _handle_op_card_drop(self, a: CardEndedDragging):
        if not self._show_card_drop_area:
            return
        
        if not rl.check_collision_point_rec(a.position.raylib_ref, self.op_card_drop_area):
            self._show_card_drop_area = False
            self.resolving_op_card = None
            return

        c = self.cards[a.card_id]
        assert type(c) == OpCard
        # EVENT_BUS.emit(OpCardStartResolving(self.me, a.card_id))
        self.state = StateMachine.SELECT_BOARD_CARDS
        self.resolving_op_card = c
        self.resolving_op_card.tween_scale(1.5)
        self.resolving_op_card.tween_center(self.resolving_op_center, 0.4)
        self._show_card_drop_area = False

    def sync(self, gw: GameView, action: GameAction):
        """Called by MatchManager after state changes."""
        self.gw = gw
        
        # Update all managers with the new redacted views
        for pid, pview in gw.players.items():
            self.decks[pid].sync(pview)
            self.boards[pid].sync(pview.board, self.cards)
            self.dps[pid].sync(pview) # completely inutile for now
            if pid == self.me:
                self.hands[pid].sync(pview)
            
            # # # If you want HandManager to animate the new card:
            # if pid == action.player_id:
            #     self.hands[pid].on_action(action, pview)
            # else:
            #     self.hands[pid].sync(pview)

    def _reset_board_slots(self):
        for board in self.boards.values():
            for slot in board.slotgrid.values():
                slot.highlighted = False

    def update(self, dt: float):
        Printer.print(rl.get_mouse_position().x, rl.get_mouse_position().y)
        for deck in self.decks.values():
            deck.update(dt)
        for hand in self.hands.values():
            hand.update(dt)
        if self.state == StateMachine.NORMAL:
            for board in self.boards.values():
                board.update(dt)
            for dp in self.dps.values():
                dp.update(dt)

        if self.state == StateMachine.SELECT_BOARD_CARDS:
            self.confirm_btn.update(dt)
            self.cancel_btn.update(dt)
            if self.cancel_btn.is_clicked:
                self.state = StateMachine.NORMAL
                assert self.resolving_op_card is not None
                EVENT_BUS.emit(CardShouldSnapBack(self.resolving_op_card, reason="Canceled operator resolve"))
                self.resolving_op_card = None
            if self.confirm_btn.is_clicked:
                assert self.resolving_op_card is not None
                EVENT_BUS.emit(PlayOpCardAction(self.me, self.resolving_op_card.card_id, [c for c, _ in self.selected_board_cards]))
                self.state = StateMachine.NORMAL
                self.resolving_op_card = None
                self.selected_board_cards = []
                self._reset_board_slots()

            # Inside update(), under SELECT_BOARD_CARDS
            if rl.is_mouse_button_pressed(rl.MouseButton.MOUSE_BUTTON_LEFT):
                mp = rl.get_mouse_position()
                for pid, board in self.boards.items():
                    for slot in board.slotgrid.values():
                        if not slot.is_free() and rl.check_collision_point_rec(mp, slot.rec):
                            assert slot.content is not None
                            target = (slot.content.card_id, pid)
                            
                            # Toggle selection
                            if target in self.selected_board_cards:
                                self.selected_board_cards.remove(target)
                                slot.highlighted = False
                            else:
                                # Enforce same owner
                                if len(self.selected_board_cards) > 0:
                                    owner = self.selected_board_cards[0][1]
                                    if pid != owner:
                                        Printer.print("Can only select cards from the same board!", color=rl.RED)
                                        break
                                self.selected_board_cards.append(target)
                                slot.highlighted = True
                            break

    def render(self, logical_texture: rl.RenderTexture | None = None) -> None:
        for board in self.boards.values():
            board.render(logical_texture)
        if self.state == StateMachine.NORMAL:
            for hand in self.hands.values():
                hand.render(logical_texture)
            for deck in self.decks.values():
                deck.render(logical_texture)
            for dp in self.dps.values():
                dp.render(logical_texture)
                
        if self.state == StateMachine.SELECT_BOARD_CARDS:
            assert self.resolving_op_card is not None
            self.resolving_op_card.render(logical_texture)
            self.confirm_btn.render(logical_texture)
            self.cancel_btn.render(logical_texture)

        if self.gw.turn == self.me:
            text = f"Actions left: {self.gw.n_actions_left}"
            pos = rl.Vector2(40, self.lh - 40)  # bottom-left corner
            rl.draw_text_ex(
                self.sm.font, text, pos, 24, 1.0, rl.WHITE
            )  # if you have a custom font; else:
            # rl.draw_text(text, int(pos.x), int(pos.y), 24, rl.WHITE)

        if self._show_card_drop_area:
            rl.draw_rectangle_rounded_lines(self.op_card_drop_area, 0.1, 0, rl.GREEN)
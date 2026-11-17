from enum import Enum

import pyray as rl

from draw_debug import draw_debug
from entities.base import Entity
from entities.card.base import BaseCard, CardId
from entities.card.op_card import OperatorCard
from entities.card.spell_card import SpellCard
from entities.game_manager.actions import *
from entities.game_manager.dataclasses import GameView
from entities.game_manager.events import EVENT_BUS
from entities.managers.board_manager import BoardManager
from entities.managers.category_manager import CategoryManager
from entities.managers.deck_manager import DeckManager
from entities.managers.discard_pile_manager import DiscardPileManager
from entities.managers.hand_manager import HandManager
from entities.managers.op_spell_drop_zone import OpSpellDrop
from entities.managers.ring_manager import RingManager
from entities.player import PlayerId
from entities.ui.button import UIButton
from interfaces import DropResult, DropZone
from mathematics.base import Category
from mathematics.ring import ZZ
from mathematics.vector import Vector2
from Settings import WINDOW
from state_manager import StateManager


class StateMachine(Enum):
    NORMAL              = 0
    SELECT_BOARD_CARDS  = 1


class GameViewRenderer(Entity):
    def __init__(self, gw: GameView, sm: StateManager, cards: dict[CardId, BaseCard]) -> None:
        self.gw = gw
        self.lh, self.lw = WINDOW["L_HEIGHT"], WINDOW["L_WIDTH"]
        self.me = gw.me
        self.op = next(p for p in gw.players if p != self.me)
        self.cards = cards
        self.sm = sm

        self.state = StateMachine.NORMAL # STATE MACHINE
        
        # Dictionaries to hold managers for ALL players
        self.hands:         dict[PlayerId, HandManager]         = {}
        self.decks:         dict[PlayerId, DeckManager]         = {}
        self.boards:        dict[PlayerId, BoardManager]        = {}
        self.dps:           dict[PlayerId, DiscardPileManager]  = {}
        self.ring_man:      RingManager                         = RingManager(Vector2(200, round(self.lh * .5) + 100), sm, gw, ZZ())
        self.cat_man:       CategoryManager                     = CategoryManager(Vector2(200, round(self.lh * .5) - 100), sm, gw, Category(gw.active_category))


        # Define fixed positions (you can make this dynamic later based on player count)
        my_hand_center      = Vector2(self.lw / 2, self.lh - 80)
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
        EVENT_BUS.subscribe(CardStartedDragging, self._handle_op_spell_card_drag)
        EVENT_BUS.subscribe(CardEndedDragging, self._on_card_ended_dragging)
        EVENT_BUS.subscribe(OpCardStartResolving, self._on_op_spell_card_resolve)

        self.resolving_card:     OperatorCard | SpellCard | None = None
        self.resolving_card_center:   Vector2        = Vector2(200, self.lh / 2)
        self.op_spell_drop: OpSpellDrop                         = OpSpellDrop(self.op_card_drop_area, self.resolving_card_center, self.me)
        self.drop_zones:    list[DropZone]                      = [self.ring_man, self.op_spell_drop]
        self.drop_zones.append(self.boards[self.me]) # FOR NOW JUST USE MY BOARD; CANNOT PLAY CARDS INSIDE ENEMY BOARD TODO
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

    def _handle_op_spell_card_drag(self, a: CardStartedDragging):
        if type(a.card) in { OperatorCard, SpellCard }:
            self._show_card_drop_area = True
            self.op_spell_drop.is_visible = True

    def _on_card_ended_dragging(self, act: CardEndedDragging) -> None:
        for zone in self.drop_zones:
            result = zone.try_accept_drop(act)
            # print(
            #     f"[DND] drop card=#{act.card.card_id} zone={type(zone).__name__} "
            #     f"result={result.name} at={act.position}"
            # )
            
            if result == DropResult.Accepted:
                return  # Handled cleanly!
                
            if result == DropResult.InsideInvalid:
                # Optional: self.emit(PlayErrorSound())
                break   # Stop checking other zones; it hit a valid zone but failed rules

        # Reached if all zones returned Ignored, or one returned Invalid
        EVENT_BUS.emit(CardShouldSnapBack(act.card))
        self.op_spell_drop.is_visible = False
        self._show_card_drop_area = False


    def _on_op_spell_card_resolve(self, action: OpCardStartResolving) -> None:
        c = self.cards[action.card_id]
        assert c is not None
        assert type(c) in {OperatorCard, SpellCard}
        self.state = StateMachine.SELECT_BOARD_CARDS
        self.resolving_card = c
        self.resolving_card.tween_scale(1.5)
        self.resolving_card.tween_center(self.resolving_card_center, 0.4)
        self.resolving_card.tween_rotation(0.0, 0.4)
        self._show_card_drop_area = False
        self.op_spell_drop.is_visible = False

    def sync(self, gw: GameView, action: GameAction | None = None):
        """Called by MatchManager after state changes."""
        draw_debug(
            "Renderer.sync begin",
            f"action={type(action).__name__ if action is not None else None}",
            f"actor={getattr(action, 'player_id', None)}",
        )
        self.gw = gw
        
        # Update all managers with the new redacted views
        for pid, pview in gw.players.items():
            self.decks[pid].sync(pview)
            self.boards[pid].sync(pview.board, self.cards)
            self.dps[pid].sync(pview) # completely inutile for now
            if pid == self.me:
                self.hands[pid].sync(gw)

        self.ring_man.sync(gw)
        self.cat_man.sync(gw)
            
            # # # If you want HandManager to animate the new card:
            # if pid == action.player_id:
            #     self.hands[pid].on_action(action, pview)
            # else:
            #     self.hands[pid].sync(pview)
        draw_debug("Renderer.sync end")

    def _reset_board_slots(self):
        for board in self.boards.values():
            for slot in board.slotgrid.values():
                slot.highlighted = False

    def update(self, dt: float):
        # Printer.print(rl.get_mouse_position().x, rl.get_mouse_position().y)
        for deck in self.decks.values():
            deck.update(dt)
        for hand in self.hands.values():
            hand.update(dt)
        self.ring_man.update(dt)
        self.cat_man.update(dt)
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
                assert self.resolving_card is not None
                self.selected_board_cards = []
                self._reset_board_slots()
                EVENT_BUS.emit(CardShouldSnapBack(self.resolving_card, reason="Canceled operator resolve"))
                self.resolving_card = None
            if self.confirm_btn.is_clicked:
                assert self.resolving_card is not None
                if isinstance(self.resolving_card, SpellCard):
                    EVENT_BUS.emit(PlaySpellCardAction(self.me, self.resolving_card.card_id, [c for c, _ in self.selected_board_cards]))
                elif isinstance(self.resolving_card, OperatorCard):
                    EVENT_BUS.emit(PlayOpCardAction(self.me, self.resolving_card.card_id, [c for c, _ in self.selected_board_cards]))
                self.state = StateMachine.NORMAL
                self.resolving_card = None
                self.selected_board_cards = []
                self._reset_board_slots()

            # Inside update(), under SELECT_BOARD_CARDS
            if rl.is_mouse_button_pressed(rl.MouseButton.MOUSE_BUTTON_LEFT):
                mp = rl.get_mouse_position()
                for pid, board in self.boards.items():
                    for slot in board.slotgrid.values():
                        if not slot.is_free and rl.check_collision_point_rec(mp, slot.rec):
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
                                        # Printer.print("Can only select cards from the same board!", color=rl.RED)
                                        break
                                self.selected_board_cards.append(target)
                                slot.highlighted = True
                            break

    def render(self, logical_texture: rl.RenderTexture | None = None) -> None:
        # draw_debug(
        #     "Renderer.render",
        #     "hands=" + repr({
        #         pid: [hand._debug_card(card) for card in hand.cards]
        #         for pid, hand in self.hands.items()
        #     }),
        #     "occupied_slots=" + repr({
        #         pid: {
        #             coord: slot.content.card_id
        #             for coord, slot in board.slotgrid.items()
        #             if slot.content is not None
        #         }
        #         for pid, board in self.boards.items()
        #     }),
        #     "slot_states=" + repr({
        #         pid: {
        #             coord: {
        #                 "center": slot.center,
        #                 "highlighted": slot.highlighted,
        #                 "content": None if slot.content is None else {
        #                     f"{slot.content.card_id}@{slot.content.center}"
        #                 },
        #             }
        #             for coord, slot in board.slotgrid.items()
        #         }
        #         for pid, board in self.boards.items()
        #     }),
        # )
        dirty_cards = [card for card in self.cards.values() if card.texture_is_dirty]
        for card in dirty_cards:
            card.bake_texture()
        # bake_texture() ends texture mode and returns to the window target.
        # Resume the logical scene target before drawing any board/hand elements.
        if dirty_cards and logical_texture is not None:
            rl.begin_texture_mode(logical_texture)
            draw_debug(
                "Renderer restored logical target after prebaking",
                f"cards={[card.card_id for card in dirty_cards]}",
            )
        for board in self.boards.values():
            board.render(logical_texture)
        if self.state == StateMachine.NORMAL:
            self.ring_man.render(logical_texture)
            self.cat_man.render(logical_texture)
            for hand in self.hands.values():
                hand.render(logical_texture)
            for deck in self.decks.values():
                deck.render(logical_texture)
            for dp in self.dps.values():
                dp.render(logical_texture)
                
        if self.state == StateMachine.SELECT_BOARD_CARDS:
            assert self.resolving_card is not None
            self.resolving_card.render(logical_texture)
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

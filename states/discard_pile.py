from pyray import RenderTexture
import pyray as rl

from entities.card.base import BaseCard, CardId
from entities.discard_pile import DiscardPile
from mathematics.vector import Vector2
from state_manager import StateManager
from states.base import State
from entities.ui.button import UIButton  # adjust import path


class DiscardPileDetailState(State):
    CARD_GAP = 12
    MARGIN = 40
    HEADER_HEIGHT = 60

    def __init__(
        self,
        game: StateManager,
        discard_pile: DiscardPile,
        cards: dict[CardId, BaseCard]
    ) -> None:
        
        super().__init__(game)
        self.dp = discard_pile
        self.cards = cards
        self.dp_cards = [self.cards[cid] for cid in self.dp]
        if len(self.dp_cards) > 0:
            self.gy_center = Vector2(vect=self.dp_cards[0].center)
        self.card_w, self.card_h = BaseCard.DIMENSIONS
        screen_w = rl.get_screen_width()
        screen_h = rl.get_screen_height()
        usable_w = screen_w - 2 * self.MARGIN
        usable_h = screen_h - self.HEADER_HEIGHT - self.MARGIN - 80
        cols = max(1, (usable_w + self.CARD_GAP) // (self.card_w + self.CARD_GAP))
        rows = max(1, (usable_h + self.CARD_GAP) // (self.card_h + self.CARD_GAP))


        total_rows = (len(self.dp) + cols - 1) // cols if self.dp else 0
        if total_rows > rows:
            wheel = rl.get_mouse_wheel_move()
            self._scroll_offset += wheel * 60
            max_scroll = (total_rows - rows) * (self.card_h + self.CARD_GAP)
            self._scroll_offset = max(0, min(self._scroll_offset, max_scroll))
        else:
            self._scroll_offset = 0
        scroll_y = int(self._scroll_offset)

        grid_origin_y = self.HEADER_HEIGHT - scroll_y
        for i, card in enumerate(self.dp_cards):
            card.tween_scale(1.0)
            card.tween_rotation(0.0)
            col = i % cols
            row = i // cols
            cx = self.MARGIN + col * (self.card_w + self.CARD_GAP) + self.card_w / 2
            cy = grid_origin_y + row * (self.card_h + self.CARD_GAP) + self.card_h / 2
            
            if cy + self.card_h / 2 < self.HEADER_HEIGHT:
                continue
            if cy - self.card_h / 2 > screen_h - 100:
                continue
            
            if card is None:
                continue
            card.tween_center(Vector2(cx, cy))
        self._scroll_offset = 0.0


        btn_w, btn_h = 140, 48
        self.exit_button = UIButton(
            text="Back",
            rect=rl.Rectangle(
                screen_w - btn_w - 20,
                screen_h - btn_h - 20,
                btn_w,
                btn_h,
            ),
            font=self.game.font,
            color=rl.Color(180, 60, 60, 255),
        )

    def update(self, dt: float) -> None:
        for card in self.dp_cards:
            card.update(dt)
        self.exit_button.update(dt)
        if self.exit_button.is_clicked:
            for card in self.dp_cards:
                card.place_card(self.gy_center)
            self.game.exit_state()

    def render(self, logical_texture: RenderTexture | None = None) -> None:
        rl.clear_background(rl.Color(25, 25, 30, 255))

        title = f"Discard Pile ({len(self.dp)})"
        rl.draw_text_ex(
            self.game.font, title, rl.Vector2(self.MARGIN, 20), 28, 1.0, rl.WHITE
        )

        for card in self.dp_cards:
            card.render(logical_texture)

        self.exit_button.render(logical_texture)
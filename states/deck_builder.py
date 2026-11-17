from typing import Any, Callable

import pyray as rl

from entities.ring_inputs.base import BaseElementInput
from entities.ring_inputs.integer_input import IntegerInput
from entities.ring_inputs.fraction_input import FractionInput
from entities.ring_inputs.polynomial_input import PolynomialInput
from entities.ui.button import UIButton
from mathematics.base import CommUnitRing
from mathematics.ring import ZZ, QQ, PolyRing
from state_manager import StateManager
from states.base import State


# ---------------------------------------------------------------------------
# Small display helpers
# ---------------------------------------------------------------------------

def _ring_label(ring: CommUnitRing) -> str:
    return getattr(ring, "typst_str", str(ring))


def _value_label(value: Any) -> str:
    # typst_str is usually more readable than repr() for these ring elements,
    # e.g. "3 x^2 + x + 1" rather than "Polynomial({0: 1, ...})".
    return getattr(value, "typst_str", str(value))


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class DeckBuilderState(State):
    """
    Simple deck-builder UI.

    Lets the user append ring elements (integers, rationals, polynomials over
    ZZ or QQ) using the existing `ring_inputs` widgets. Entries are shown in a
    table with a per-row Remove button. Press Done to commit and exit.

    The collected entries are `(ring, value)` pairs — convert them to real
    cards (e.g. `EORCard(self.game, ring, value)`) wherever you consume them.
    """

    MARGIN       = 40
    HEADER_HEIGHT = 90
    ADD_BTN_H    = 44
    ADD_BTN_W    = 160
    ADD_BTN_GAP  = 12
    ROW_H        = 44
    ROW_GAP      = 4

    def __init__(
        self,
        game:     StateManager,
        on_done:  Callable[[list[tuple[CommUnitRing, Any]]], None] | None = None,
    ) -> None:
        super().__init__(game)
        self.entries: list[tuple[CommUnitRing, Any]] = []
        self.active_input: BaseElementInput | None = None
        self.on_done = on_done

        sw, sh = rl.get_screen_width(), rl.get_screen_height()

        # --- Add buttons ---
        y = self.HEADER_HEIGHT + 20
        x = self.MARGIN
        self.add_buttons: list[tuple[UIButton, str]] = []
        for label, kind in [
            ("+ Integer (ZZ)",  "int_zz"),
            ("+ Rational (QQ)", "rat_qq"),
            ("+ Poly / ZZ",     "poly_zz"),
            ("+ Poly / QQ",     "poly_qq"),
        ]:
            btn = UIButton(
                text  = label,
                rect  = rl.Rectangle(x, y, self.ADD_BTN_W, self.ADD_BTN_H),
                font  = self.game.font,
                color = rl.Color(50, 100, 170, 255),
            )
            self.add_buttons.append((btn, kind))
            x += self.ADD_BTN_W + self.ADD_BTN_GAP

        # --- Done button ---
        bw, bh = 140, 48
        self.done_button = UIButton(
            text  = "Done",
            rect  = rl.Rectangle(sw - bw - 20, sh - bh - 20, bw, bh),
            font  = self.game.font,
            color = rl.Color(60, 150, 90, 255),
        )

        self.remove_buttons: list[tuple[UIButton, int]] = []

    # ------------------------------------------------------------------ layout

    def _list_origin_y(self) -> float:
        return self.HEADER_HEIGHT + 20 + self.ADD_BTN_H + 30

    def _row_y(self, i: int) -> float:
        # +20 leaves room for the column-header line
        return self._list_origin_y() + 20 + i * (self.ROW_H + self.ROW_GAP)

    def _rebuild_row_buttons(self) -> None:
        sw = rl.get_screen_width()
        self.remove_buttons.clear()
        for i in range(len(self.entries)):
            y = self._row_y(i)
            rect = rl.Rectangle(sw - self.MARGIN - 110, y + 4, 110, self.ROW_H - 8)
            self.remove_buttons.append((
                UIButton("Remove", rect, self.game.font, rl.Color(160, 60, 60, 255)),
                i,
            ))

    # ------------------------------------------------------------------ spawn widget

    def _open_input(self, kind: str, anchor: rl.Rectangle) -> None:
        idx = len(self.entries)

        def _confirm_with(ring: CommUnitRing):
            def _cb(value: Any) -> None:
                self.entries.append((ring, value))
                self.active_input = None
                self._rebuild_row_buttons()
            return _cb

        def _cancel() -> None:
            self.active_input = None

        if kind == "int_zz":
            zz = ZZ()
            self.active_input = IntegerInput(
                ring          = zz,
                anchor_rect   = anchor,
                gen_name      = f"n{idx}",
                initial_value = 0,
                on_confirm    = _confirm_with(zz),
                on_cancel     = _cancel,
                tfr           = self.game.tfr,
                font          = self.game.font,
            )

        elif kind == "rat_qq":
            qq = QQ()
            self.active_input = FractionInput(
                ring          = qq,
                anchor_rect   = anchor,
                gen_name      = f"q{idx}",
                initial_value = None,        # starts as 0/1
                on_confirm    = _confirm_with(qq),
                on_cancel     = _cancel,
                tfr           = self.game.tfr,
                font          = self.game.font,
            )

        elif kind in ("poly_zz", "poly_qq"):
            coeff = ZZ() if kind == "poly_zz" else QQ()
            # PolyRing might need an explicit generator name depending on your
            # implementation; adapt these two lines if so.
            poly_ring = PolyRing(coeff)

            self.active_input = PolynomialInput(
                ring          = poly_ring,
                anchor_rect   = anchor,
                gen_name      = f"p{idx}",
                initial_value = None,
                on_confirm    = _confirm_with(poly_ring),
                on_cancel     = _cancel,
                tfr           = self.game.tfr,
                font          = self.game.font,
            )

    # ------------------------------------------------------------------ update

    def update(self, dt: float) -> None:
        # A widget is open → it owns all input (click-outside cancels it)
        if self.active_input is not None:
            self.active_input.update(dt)
            return

        # Add buttons
        for btn, kind in self.add_buttons:
            btn.update(dt)
            if btn.is_clicked:
                self._open_input(kind, btn.rect)
                return

        # Remove buttons
        for btn, i in self.remove_buttons:
            btn.update(dt)
            if btn.is_clicked:
                self.entries.pop(i)
                self._rebuild_row_buttons()
                return

        # Done
        self.done_button.update(dt)
        if self.done_button.is_clicked:
            if self.on_done is not None:
                self.on_done(self.entries)
            self.game.exit_state()

    # ------------------------------------------------------------------ render

    def render(self, logical_texture: rl.RenderTexture | None = None) -> None:
        rl.clear_background(rl.Color(22, 26, 34, 255))

        # Header
        n = len(self.entries)
        rl.draw_text_ex(
            self.game.font,
            f"Deck Builder  ({n} card{'s' if n != 1 else ''})",
            rl.Vector2(self.MARGIN, 24),
            30, 1.0, rl.WHITE,
        )

        # Add buttons
        for btn, _ in self.add_buttons:
            btn.render(logical_texture)

        # Column headers
        y0 = self._list_origin_y()
        rl.draw_text_ex(self.game.font, "#",     rl.Vector2(self.MARGIN + 12,  y0 - 4), 16, 1.0, rl.Color(140, 155, 180, 255))
        rl.draw_text_ex(self.game.font, "Value", rl.Vector2(self.MARGIN + 80,  y0 - 4), 16, 1.0, rl.Color(140, 155, 180, 255))
        rl.draw_text_ex(self.game.font, "Ring",  rl.Vector2(self.MARGIN + 400, y0 - 4), 16, 1.0, rl.Color(140, 155, 180, 255))

        # Entry rows
        sw    = rl.get_screen_width()
        max_y = rl.get_screen_height() - 90
        for i, (ring, value) in enumerate(self.entries):
            y = self._row_y(i)
            if y > max_y:
                remaining = len(self.entries) - i
                rl.draw_text_ex(
                    self.game.font,
                    f"... and {remaining} more",
                    rl.Vector2(self.MARGIN, max_y + 8),
                    16, 1.0, rl.Color(180, 180, 180, 255),
                )
                break

            rl.draw_rectangle_rounded(
                rl.Rectangle(self.MARGIN, y, sw - 2 * self.MARGIN, self.ROW_H),
                0.15, 4, rl.Color(40, 48, 65, 255),
            )
            rl.draw_text_ex(
                self.game.font, f"#{i + 1}",
                rl.Vector2(self.MARGIN + 12, y + 12),
                18, 1.0, rl.Color(140, 155, 180, 255),
            )
            rl.draw_text_ex(
                self.game.font, _value_label(value),
                rl.Vector2(self.MARGIN + 80, y + 12),
                18, 1.0, rl.WHITE,
            )
            rl.draw_text_ex(
                self.game.font, _ring_label(ring),
                rl.Vector2(self.MARGIN + 400, y + 12),
                16, 1.0, rl.Color(160, 180, 220, 255),
            )

        # Remove buttons (culled with the rows)
        for btn, i in self.remove_buttons:
            if i < len(self.entries) and self._row_y(i) <= max_y:
                btn.render(logical_texture)

        # Done
        self.done_button.render(logical_texture)

        # Active widget on top
        if self.active_input is not None:
            self.active_input.render(logical_texture)
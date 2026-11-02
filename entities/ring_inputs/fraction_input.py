# entities/ring_inputs/fraction_input.py
"""
Input popover for QQ, FractionField, and Localization ring elements.
Shows two integer fields: numerator (top) and denominator (bottom).
Tab or click switches active field. Denominator cannot be 0.
For Localization/FractionField, the denominator must not lie in the ideal
(i.e. it must be invertible in the localization).
"""
from typing import Any, Callable

import pyray as rl

from entities.ring_inputs.base import BaseElementInput
from mathematics.base import UnitaryRing
from mathematics.ring import Frac, FractionField, Localization, QQ
from tfr import TypstFormulaRenderer


class FractionInput(BaseElementInput):
    """Handles fraction input for QQ, FractionField, Localization."""

    def __init__(
        self,
        ring:          UnitaryRing,
        anchor_rect:   rl.Rectangle | None,
        gen_name:      str,
        initial_value: Any,
        on_confirm:    Callable[[Any], None],
        on_cancel:     Callable[[], None] | None = None,
        tfr:           TypstFormulaRenderer | None = None,
        font:          rl.Font | None = None,
    ) -> None:
        # Resolve initial numerator/denominator
        if isinstance(initial_value, Frac):
            self._num_str = str(initial_value.num)
            self._den_str = str(initial_value.denom)
        else:
            self._num_str = "0"
            self._den_str = "1"

        # Which field is focused: 0 = numerator, 1 = denominator
        self._focus: int = 0
        self._error: str | None = None

        super().__init__(ring, anchor_rect, gen_name, initial_value, on_confirm, on_cancel, tfr, font)

    # ------------------------------------------------------------------ layout

    def _build_layout(self) -> None:
        rx = self.rect.x
        mid_x = rx + self.w / 2.0
        center_y = (self.content_y + self.content_bot_y) / 2.0

        field_w, field_h = 180.0, 46.0
        gap = 8.0  # gap between fields and divider line

        self.box_num = rl.Rectangle(mid_x - field_w / 2.0, center_y - field_h - gap - 2, field_w, field_h)
        self.box_den = rl.Rectangle(mid_x - field_w / 2.0, center_y + gap + 2,           field_w, field_h)

        # Divider line y
        self._div_y   = center_y
        self._div_x0  = mid_x - field_w / 2.0 - 10
        self._div_x1  = mid_x + field_w / 2.0 + 10

        # Labels
        self._lbl_num_x = rx + 22
        self._lbl_y_num = self.box_num.y + (field_h - 18.0) / 2.0
        self._lbl_y_den = self.box_den.y + (field_h - 18.0) / 2.0

    # ------------------------------------------------------------------ helpers

    def _active_str(self) -> str:
        return self._num_str if self._focus == 0 else self._den_str

    def _set_active_str(self, s: str) -> None:
        if self._focus == 0:
            self._num_str = s
        else:
            self._den_str = s

    def _parse_int(self, s: str) -> int | None:
        clean = s.strip()
        if clean in ("", "-"):
            return 0
        try:
            return int(clean)
        except ValueError:
            return None

    # ------------------------------------------------------------------ BaseElementInput

    def _update_input(self, dt: float) -> None:
        mouse_pos   = rl.get_mouse_position()
        mouse_click = rl.is_mouse_button_pressed(rl.MouseButton.MOUSE_BUTTON_LEFT)

        # Tab switches focus
        if rl.is_key_pressed(rl.KeyboardKey.KEY_TAB):
            self._focus = 1 - self._focus
            self._error = None

        # Click to focus field
        if mouse_click:
            if rl.check_collision_point_rec(mouse_pos, self.box_num):
                self._focus = 0; self._error = None; return
            if rl.check_collision_point_rec(mouse_pos, self.box_den):
                self._focus = 1; self._error = None; return

        # Backspace on active field
        if rl.is_key_pressed(rl.KeyboardKey.KEY_BACKSPACE) or rl.is_key_pressed_repeat(rl.KeyboardKey.KEY_BACKSPACE):
            self._error = None
            cur = self._active_str()
            if cur:
                self._set_active_str(cur[:-1])

        # Typing
        ch = rl.get_char_pressed()
        while ch > 0:
            self._error = None
            c = chr(ch)
            cur = self._active_str()
            if c in "0123456789":
                self._set_active_str(c if cur == "0" else cur + c)
            elif c == "-":
                if cur.startswith("-"):
                    self._set_active_str(cur[1:])
                else:
                    self._set_active_str("-" + cur)
            ch = rl.get_char_pressed()

    def _render_input_area(self, mouse_pos: rl.Vector2) -> None:
        # Labels
        self.draw_text("num:", self._lbl_num_x, self._lbl_y_num, 18.0, self.COL_SUBTITLE)
        self.draw_text("den:", self._lbl_num_x, self._lbl_y_den, 18.0, self.COL_SUBTITLE)

        # Divider line
        rl.draw_line_ex(
            rl.Vector2(self._div_x0, self._div_y),
            rl.Vector2(self._div_x1, self._div_y),
            2.0, rl.Color(120, 140, 180, 200),
        )

        for idx, (box, label_str) in enumerate([
            (self.box_num, self._num_str),
            (self.box_den, self._den_str),
        ]):
            focused = (self._focus == idx)
            border  = self.COL_FIELD_BORDER if focused else rl.Color(70, 85, 115, 200)
            rl.draw_rectangle_rounded(box, 0.2, 6, self.COL_FIELD_BG)
            rl.draw_rectangle_rounded_lines_ex(box, 0.2, 6, 1.5, border)

            disp = label_str if label_str else "0"
            tw   = self.measure_text_w(disp, 28.0)
            tx   = box.x + (box.width - tw) / 2.0
            ty   = box.y + (box.height - 28.0) / 2.0
            self.draw_text(disp, tx, ty, 28.0, rl.WHITE)

            # Blinking cursor on focused field
            if focused and int(self.cursor_blink_time * 2.5) % 2 == 0:
                cx = int(tx + tw + 4)
                cy = int(ty + 2)
                rl.draw_line(cx, cy, cx, cy + 24, self.COL_ACCENT)

        # Error / validation warning (denominator zero, or ideal membership)
        den_val = self._parse_int(self._den_str)
        err: str | None = None
        if den_val == 0:
            err = "Denominator cannot be 0"
        elif self._error:
            err = self._error
        if err:
            self.draw_text(
                err,
                self.rect.x + 22, self.content_bot_y - 22, 15.0,
                rl.Color(239, 68, 68, 255),
            )

    def current_value(self) -> Any:
        num = self._parse_int(self._num_str) or 0
        den = self._parse_int(self._den_str) or 1
        if den == 0:
            den = 1  # safe fallback

        frac = Frac(num, den)

        # For QQ, FractionField, and Localization the element is a Frac
        # interpreted by the containing ring. For Localization/FractionField,
        # additionally enforce that the denominator is invertible (not in the
        # ideal). If this raises, the value was not valid for this ring; the
        # caller is responsible for having blocked confirm beforehand.
        if isinstance(self.ring, Localization):
            self.ring.validate_element(frac)

        return frac

    def _do_confirm(self) -> None:
        den_val = self._parse_int(self._den_str)
        if den_val == 0:
            self._error = "Denominator cannot be 0"
            return  # block confirm if denominator is zero

        # For Localization/FractionField, the denominator must not lie in the
        # ideal (i.e. it must be invertible in the localization).
        if isinstance(self.ring, Localization):
            num_val = self._parse_int(self._num_str) or 0
            candidate = Frac(num_val, den_val)
            try:
                self.ring.validate_element(candidate)
            except ValueError as exc:
                self._error = str(exc)
                return

        self._error = None
        super()._do_confirm()
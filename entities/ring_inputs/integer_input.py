# entities/ring_inputs/integer_input.py
"""
Input popover for ZZ and ZZn ring elements.
Provides a stepper (+/-), keyboard input, and quick-select preset chips.
"""
from typing import Any, Callable

import pyray as rl

from entities.ring_inputs.base import BaseElementInput
from mathematics.base import CommUnitRing
from mathematics.ring import ZZ, ZZn
from tfr import TypstFormulaRenderer


class IntegerInput(BaseElementInput):
    """Handles integer input for ZZ and ZZn rings."""

    def __init__(
        self,
        ring:          CommUnitRing,
        anchor_rect:   rl.Rectangle | None,
        gen_name:      str,
        initial_value: Any,
        on_confirm:    Callable[[Any], None],
        on_cancel:     Callable[[], None] | None = None,
        tfr:           TypstFormulaRenderer | None = None,
        font:          rl.Font | None = None,
    ) -> None:
        # Resolve initial int
        init_int = initial_value if isinstance(initial_value, int) else 0
        self._value: int = init_int
        self._input_str: str = str(init_int)

        super().__init__(ring, anchor_rect, gen_name, initial_value, on_confirm, on_cancel, tfr, font)

    # ------------------------------------------------------------------ helpers

    def _is_finite(self) -> bool:
        return isinstance(self.ring, ZZn)

    def _reduce(self, val: int) -> int:
        if isinstance(self.ring, ZZn):
            return self.ring.reduce_mod(val)
        return val

    def _sync_from_str(self) -> bool:
        clean = self._input_str.strip()
        if clean in ("", "-"):
            self._value = 0
            return True
        try:
            self._value = self._reduce(int(clean))
            return True
        except ValueError:
            return False

    def _step(self, delta: int) -> None:
        self._sync_from_str()
        self._value = self._reduce(self._value + delta)
        self._input_str = str(self._value)

    # ------------------------------------------------------------------ BaseElementInput

    def _build_layout(self) -> None:
        rx, ry = self.rect.x, self.rect.y

        field_w = 160.0
        field_h = 48.0
        field_x = rx + (self.w - field_w) / 2.0
        field_y = self.content_y + 12.0

        self.btn_minus = rl.Rectangle(field_x - 56, field_y, 48, 48)
        self.box_input = rl.Rectangle(field_x, field_y, field_w, field_h)
        self.btn_plus  = rl.Rectangle(field_x + field_w + 8, field_y, 48, 48)

        # Presets
        presets = self._compute_presets()
        self._presets: list[int] = presets
        chip_y = field_y + field_h + 16.0
        chip_w, chip_h, chip_sp = 46.0, 32.0, 8.0
        total_w = len(presets) * chip_w + max(0, len(presets) - 1) * chip_sp
        cx0 = rx + (self.w - total_w) / 2.0
        self._preset_rects: list[tuple[rl.Rectangle, int]] = []
        for i, val in enumerate(presets):
            self._preset_rects.append((rl.Rectangle(cx0 + i * (chip_w + chip_sp), chip_y, chip_w, chip_h), val))

    def _compute_presets(self) -> list[int]:
        if isinstance(self.ring, ZZn):
            n = self.ring.n
            return list(range(n)) if n <= 8 else []
        return [-2, -1, 0, 1, 2, 3]

    def _update_input(self, dt: float) -> None:
        mouse_pos   = rl.get_mouse_position()
        mouse_click = rl.is_mouse_button_pressed(rl.MouseButton.MOUSE_BUTTON_LEFT)

        # Arrow stepping
        if rl.is_key_pressed(rl.KeyboardKey.KEY_UP) or rl.is_key_pressed_repeat(rl.KeyboardKey.KEY_UP):
            self._step(1)
        elif rl.is_key_pressed(rl.KeyboardKey.KEY_DOWN) or rl.is_key_pressed_repeat(rl.KeyboardKey.KEY_DOWN):
            self._step(-1)

        # Backspace
        if rl.is_key_pressed(rl.KeyboardKey.KEY_BACKSPACE) or rl.is_key_pressed_repeat(rl.KeyboardKey.KEY_BACKSPACE):
            if self._input_str:
                self._input_str = self._input_str[:-1]
                self._sync_from_str()

        # Typing
        ch = rl.get_char_pressed()
        while ch > 0:
            c = chr(ch)
            if c in "0123456789":
                self._input_str = c if self._input_str == "0" else self._input_str + c
                self._sync_from_str()
            elif c == "-" and not self._is_finite():
                if self._input_str.startswith("-"):
                    self._input_str = self._input_str[1:]
                else:
                    self._input_str = "-" + self._input_str
                self._sync_from_str()
            ch = rl.get_char_pressed()

        # Mouse clicks on stepper / chips
        if mouse_click:
            if rl.check_collision_point_rec(mouse_pos, self.btn_minus):
                self._step(-1); return
            if rl.check_collision_point_rec(mouse_pos, self.btn_plus):
                self._step(1); return
            for chip_rect, chip_val in self._preset_rects:
                if rl.check_collision_point_rec(mouse_pos, chip_rect):
                    self._value = chip_val
                    self._input_str = str(chip_val)
                    return

    def _render_input_area(self, mouse_pos: rl.Vector2) -> None:
        # [-] button
        minus_h = rl.check_collision_point_rec(mouse_pos, self.btn_minus)
        rl.draw_rectangle_rounded(self.btn_minus, 0.2, 6, self.COL_STEPPER_H if minus_h else self.COL_STEPPER_BG)
        rl.draw_rectangle_rounded_lines_ex(self.btn_minus, 0.2, 6, 1.2, self.COL_STEPPER_BRD)
        mw = self.measure_text_w("-", 28.0)
        self.draw_text("-", self.btn_minus.x + (self.btn_minus.width - mw) / 2.0, self.btn_minus.y + 8, 28.0, rl.WHITE)

        # [+] button
        plus_h = rl.check_collision_point_rec(mouse_pos, self.btn_plus)
        rl.draw_rectangle_rounded(self.btn_plus, 0.2, 6, self.COL_STEPPER_H if plus_h else self.COL_STEPPER_BG)
        rl.draw_rectangle_rounded_lines_ex(self.btn_plus, 0.2, 6, 1.2, self.COL_STEPPER_BRD)
        pw = self.measure_text_w("+", 28.0)
        self.draw_text("+", self.btn_plus.x + (self.btn_plus.width - pw) / 2.0, self.btn_plus.y + 8, 28.0, rl.WHITE)

        # Input box
        rl.draw_rectangle_rounded(self.box_input, 0.2, 6, self.COL_FIELD_BG)
        rl.draw_rectangle_rounded_lines_ex(self.box_input, 0.2, 6, 1.5, self.COL_FIELD_BORDER)
        disp = self._input_str if self._input_str else "0"
        tw = self.measure_text_w(disp, 32.0)
        tx = self.box_input.x + (self.box_input.width - tw) / 2.0
        ty = self.box_input.y + (self.box_input.height - 32.0) / 2.0
        self.draw_text(disp, tx, ty, 32.0, rl.WHITE)
        # Cursor blink
        if int(self.cursor_blink_time * 2.5) % 2 == 0:
            rl.draw_line(int(tx + tw + 4), int(ty + 3), int(tx + tw + 4), int(ty + 29), self.COL_ACCENT)

        # Preset chips
        for chip_rect, chip_val in self._preset_rects:
            active = (self._value == chip_val) and (self._input_str == str(chip_val))
            hover  = rl.check_collision_point_rec(mouse_pos, chip_rect)
            if active:
                chip_bg  = rl.Color(14, 116, 144, 255)
                chip_brd = rl.Color(56, 189, 248, 255)
            elif hover:
                chip_bg  = rl.Color(48, 58, 80, 255)
                chip_brd = rl.Color(100, 120, 160, 255)
            else:
                chip_bg  = rl.Color(32, 38, 52, 255)
                chip_brd = rl.Color(60, 72, 98, 255)
            rl.draw_rectangle_rounded(chip_rect, 0.35, 6, chip_bg)
            rl.draw_rectangle_rounded_lines_ex(chip_rect, 0.35, 6, 1.0, chip_brd)
            ctxt = str(chip_val)
            cw = self.measure_text_w(ctxt, 18.0)
            self.draw_text(ctxt,
                chip_rect.x + (chip_rect.width - cw) / 2.0,
                chip_rect.y + (chip_rect.height - 18.0) / 2.0,
                18.0, rl.WHITE)

    def current_value(self) -> int:
        self._sync_from_str()
        return self._value

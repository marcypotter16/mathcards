# entities/ring_inputs/base.py
"""
Shared base class for all ring-element input popovers.
Subclasses override _build_layout() and _render_input_area() / _update_input(dt).
"""
from typing import Any, Callable

import pyray as rl

from entities.base import Entity
from mathematics.base import UnitaryRing
from tfr import TypstFormulaRenderer


class BaseElementInput(Entity):
    """
    Draws the popover chrome (shadow, body, header, close button, Cancel/Confirm).
    Subclasses implement:
      - _build_layout()     → compute sub-rects for their controls
      - _update_input(dt)   → handle keyboard/mouse for their input area
      - _render_input_area() → draw their input controls
      - current_value()     → return the parsed ring element
    """

    # Palette
    COL_BG          = rl.Color(28,  33,  46, 252)
    COL_BORDER      = rl.Color(70,  85, 115, 255)
    COL_SHADOW      = rl.Color( 0,   0,   0,  90)
    COL_ACCENT      = rl.Color(56, 189, 248, 255)
    COL_SUBTITLE    = rl.Color(160, 175, 200, 255)
    COL_BTN_CANCEL  = rl.Color(42,  50,  68, 255)
    COL_BTN_CANCEL_H= rl.Color(55,  65,  85, 255)
    COL_BTN_CONFIRM = rl.Color(29,  78, 216, 255)
    COL_BTN_CONFIRM_H=rl.Color(37,  99, 235, 255)
    COL_FIELD_BG    = rl.Color(16,  20,  28, 255)
    COL_FIELD_BORDER= rl.Color(56, 189, 248, 220)
    COL_STEPPER_BG  = rl.Color(38,  45,  62, 255)
    COL_STEPPER_H   = rl.Color(52,  62,  85, 255)
    COL_STEPPER_BRD = rl.Color(80,  95, 130, 255)

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
        super().__init__()
        self.ring        = ring
        self.anchor_rect = anchor_rect
        self.gen_name    = str(gen_name)
        self.on_confirm  = on_confirm
        self.on_cancel   = on_cancel
        self.tfr         = tfr
        self.font: rl.Font = font if font is not None else rl.get_font_default()

        self.w: float = 410.0
        self.h: float = 290.0

        # Position
        if anchor_rect is not None:
            tx = anchor_rect.x + anchor_rect.width + 24
            ty = anchor_rect.y + (anchor_rect.height / 2.0) - (self.h / 2.0)
            if tx + self.w > 1920 - 30:
                tx = anchor_rect.x - self.w - 24
            ty = max(30.0, min(ty, 1080.0 - self.h - 30.0))
            self.rect = rl.Rectangle(tx, ty, self.w, self.h)
        else:
            self.rect = rl.Rectangle(
                (1920.0 - self.w) / 2.0,
                (1080.0 - self.h) / 2.0,
                self.w, self.h,
            )

        self.cursor_blink_time: float = 0.0

        # Chrome buttons (computed in _build_chrome_layout)
        self._build_chrome_layout()

        # Subclass layout
        self._build_layout()

    # ------------------------------------------------------------------ helpers

    def draw_text(self, text: str, x: float, y: float, size: float, color: rl.Color, spacing: float = 1.0) -> None:
        rl.draw_text_ex(self.font, text, rl.Vector2(x, y), size, spacing, color)

    def measure_text_w(self, text: str, size: float, spacing: float = 1.0) -> float:
        return rl.measure_text_ex(self.font, text, size, spacing).x

    # ------------------------------------------------------------------ chrome layout

    def _build_chrome_layout(self) -> None:
        rx, ry = self.rect.x, self.rect.y
        self.btn_close  = rl.Rectangle(rx + self.w - 40, ry + 12, 28, 28)

        btn_h = 42.0
        btn_y = ry + self.h - btn_h - 18.0
        gap   = 16.0
        btn_w = (self.w - 40.0 - gap) / 2.0
        self.btn_cancel  = rl.Rectangle(rx + 20.0,               btn_y, btn_w, btn_h)
        self.btn_confirm = rl.Rectangle(rx + 20.0 + btn_w + gap, btn_y, btn_w, btn_h)

        # Content area: between header and buttons
        self.content_y     = ry + 72.0
        self.content_bot_y = btn_y - 8.0

    # ------------------------------------------------------------------ to override

    def _build_layout(self) -> None:
        """Subclasses compute control rects here (called after chrome layout)."""
        pass

    def _update_input(self, dt: float) -> None:
        """Subclasses handle keyboard/mouse for their specific input area."""
        pass

    def _render_input_area(self, mouse_pos: rl.Vector2) -> None:
        """Subclasses draw their input controls here."""
        pass

    def current_value(self) -> Any:
        """Subclasses return the currently entered ring element."""
        return 0

    def _do_confirm(self) -> None:
        self.on_confirm(self.current_value())

    def _do_cancel(self) -> None:
        if self.on_cancel is not None:
            self.on_cancel()

    # ------------------------------------------------------------------ Entity interface

    def update(self, dt: float) -> None:
        self.cursor_blink_time += dt
        mouse_pos    = rl.get_mouse_position()
        mouse_click  = rl.is_mouse_button_pressed(rl.MouseButton.MOUSE_BUTTON_LEFT)

        # Global keys
        if rl.is_key_pressed(rl.KeyboardKey.KEY_ENTER):
            self._do_confirm(); return
        if rl.is_key_pressed(rl.KeyboardKey.KEY_ESCAPE):
            self._do_cancel(); return

        # Click outside → cancel
        if mouse_click:
            inside  = rl.check_collision_point_rec(mouse_pos, self.rect)
            on_anch = self.anchor_rect and rl.check_collision_point_rec(mouse_pos, self.anchor_rect)
            if not inside and not on_anch:
                self._do_cancel(); return

            if rl.check_collision_point_rec(mouse_pos, self.btn_close):
                self._do_cancel(); return
            if rl.check_collision_point_rec(mouse_pos, self.btn_cancel):
                self._do_cancel(); return
            if rl.check_collision_point_rec(mouse_pos, self.btn_confirm):
                self._do_confirm(); return

        # Delegate to subclass
        self._update_input(dt)

    def render(self, logical_texture: rl.RenderTexture | None = None) -> None:
        mouse_pos = rl.get_mouse_position()

        # Bezier connector
        if self.anchor_rect is not None:
            ax = self.anchor_rect.x + self.anchor_rect.width
            ay = self.anchor_rect.y + self.anchor_rect.height / 2.0
            px = self.rect.x
            py = self.rect.y + self.rect.height / 2.0
            if self.rect.x < self.anchor_rect.x:
                ax = self.anchor_rect.x
                px = self.rect.x + self.rect.width
            rl.draw_line_bezier(
                rl.Vector2(ax, ay), rl.Vector2(px, py),
                3.0, rl.Color(56, 189, 248, 180),
            )

        # Shadow
        rl.draw_rectangle_rounded(
            rl.Rectangle(self.rect.x + 4, self.rect.y + 6, self.rect.width, self.rect.height),
            0.08, 12, self.COL_SHADOW,
        )
        # Body
        rl.draw_rectangle_rounded(self.rect, 0.08, 12, self.COL_BG)
        rl.draw_rectangle_rounded_lines_ex(self.rect, 0.08, 12, 1.8, self.COL_BORDER)

        # Header
        title = f"Assign Image: phi({self.gen_name})"
        self.draw_text(title, self.rect.x + 22, self.rect.y + 16, 22.0, self.COL_ACCENT)
        ring_label = getattr(self.ring, "typst_str", str(self.ring))
        self.draw_text(f"Codomain: in {ring_label}", self.rect.x + 22, self.rect.y + 46, 16.0, self.COL_SUBTITLE)

        # Close [x]
        close_hover = rl.check_collision_point_rec(mouse_pos, self.btn_close)
        self.draw_text(
            "x", self.btn_close.x + 8, self.btn_close.y + 3, 20.0,
            rl.Color(239, 68, 68, 255) if close_hover else rl.Color(130, 140, 160, 255),
        )

        # Input area (subclass)
        self._render_input_area(mouse_pos)

        # Cancel button
        cancel_hover = rl.check_collision_point_rec(mouse_pos, self.btn_cancel)
        rl.draw_rectangle_rounded(self.btn_cancel, 0.25, 6,
            self.COL_BTN_CANCEL_H if cancel_hover else self.COL_BTN_CANCEL)
        rl.draw_rectangle_rounded_lines_ex(self.btn_cancel, 0.25, 6, 1.0, rl.Color(90, 105, 135, 255))
        cw = self.measure_text_w("Cancel", 18.0)
        self.draw_text("Cancel",
            self.btn_cancel.x + (self.btn_cancel.width - cw) / 2.0,
            self.btn_cancel.y + (self.btn_cancel.height - 18.0) / 2.0,
            18.0, rl.Color(210, 220, 240, 255))

        # Confirm button
        confirm_hover = rl.check_collision_point_rec(mouse_pos, self.btn_confirm)
        rl.draw_rectangle_rounded(self.btn_confirm, 0.25, 6,
            self.COL_BTN_CONFIRM_H if confirm_hover else self.COL_BTN_CONFIRM)
        rl.draw_rectangle_rounded_lines_ex(self.btn_confirm, 0.25, 6, 1.2, rl.Color(96, 165, 250, 255))
        ok = "Confirm (Enter)"
        ok_w = self.measure_text_w(ok, 18.0)
        self.draw_text(ok,
            self.btn_confirm.x + (self.btn_confirm.width - ok_w) / 2.0,
            self.btn_confirm.y + (self.btn_confirm.height - 18.0) / 2.0,
            18.0, rl.WHITE)

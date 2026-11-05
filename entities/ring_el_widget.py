# entities/ring_el_widget.py
"""
RingElementConstructor — thin dispatcher that picks the right input widget
based on the ring type and delegates all update/render calls to it.
"""
from typing import Any, Callable

import pyray as rl

from entities.base import Entity
from entities.ring_inputs.integer_input import IntegerInput
from entities.ring_inputs.fraction_input import FractionInput
from entities.ring_inputs.polynomial_input import PolynomialInput
from mathematics.base import CommUnitRing
from mathematics.ring import ZZ, ZZn, QQ, FractionField, Localization, PolyRing, PolyRingQuot
from tfr import TypstFormulaRenderer


class RingElementConstructor(Entity):
    """
    An interactive UI popover widget to construct and input an element of a ring.
    Dispatches to the appropriate subclass based on ring type.
    """

    def __init__(
        self,
        ring:           CommUnitRing,
        anchor_rect:    rl.Rectangle | None,
        gen_name:       str,
        initial_value:  int | Any,
        on_confirm:     Callable[[Any], None],
        on_cancel:      Callable[[], None] | None = None,
        tfr:            TypstFormulaRenderer | None = None,
        font:           rl.Font | None = None,
    ) -> None:
        super().__init__()

        kwargs = dict(
            ring=ring,
            anchor_rect=anchor_rect,
            gen_name=gen_name,
            initial_value=initial_value,
            on_confirm=on_confirm,
            on_cancel=on_cancel,
            tfr=tfr,
            font=font,
        )

        match ring:
            case PolyRingQuot() | PolyRing():
                self._delegate = PolynomialInput(**kwargs)
            case QQ() | FractionField() | Localization():
                self._delegate = FractionInput(**kwargs)
            case ZZn() | ZZ():
                self._delegate = IntegerInput(**kwargs)
            case _:
                # Fallback: treat as integer input
                self._delegate = IntegerInput(**kwargs)

    def update(self, dt: float) -> None:
        self._delegate.update(dt)

    def render(self, logical_texture: rl.RenderTexture | None = None) -> None:
        self._delegate.render(logical_texture)

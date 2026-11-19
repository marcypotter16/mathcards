from dataclasses import dataclass
from enum import StrEnum, auto
from typing import TYPE_CHECKING

import pyray as rl

if TYPE_CHECKING:
    from entities.card.base import BaseCard


class CardVisualMode(StrEnum):
    NORMAL = auto()
    HOVERED = auto()


@dataclass(frozen=True)
class CardStyle:
    glow_width: float = 0.0
    glow_alpha: float = 0.0
    max_tilt: float = 0.0
    inset: float = 0.0


@dataclass
class _CardAnimState:
    tilt_y: float = 0.0
    tilt_x: float = 0.0
    glow_width: float = 0.0
    glow_alpha: float = 0.0
    inset: float = 0.0

    @property
    def is_idle(self) -> bool:
        return (
            abs(self.tilt_y) < 0.01
            and abs(self.tilt_x) < 0.01
            and self.glow_alpha < 0.005
            and self.inset < 0.001
        )


CARD_STYLES: dict[CardVisualMode, CardStyle] = {
    CardVisualMode.NORMAL: CardStyle(),
    # Valori più discreti (max_tilt=10.0, glow_alpha=0.6) per un effetto elegante
    CardVisualMode.HOVERED: CardStyle(
        glow_width=5.0,
        glow_alpha=0.6,
        max_tilt=10.0,
        inset=0.04,
    ),
}


class CardVisualRenderer:
    """Draw shared transient card effects over each card's baked texture."""

    def __init__(self, shader: rl.Shader) -> None:
        self.shader = shader
        self._locations = {
            name: rl.get_shader_location(shader, name)
            for name in (
                "glowColor", "glowWidth", "textureSize", "y_rot", "x_rot",
                "fov", "inset", "cardCenter", "cardSize",
            )
        }
        self._states: dict[int, _CardAnimState] = {}

    @staticmethod
    def _mode_for(card: BaseCard) -> CardVisualMode:
        return CardVisualMode.HOVERED if card.state.is_hovered else CardVisualMode.NORMAL

    def _target_tilt(self, card: BaseCard, width: float, height: float, max_tilt: float) -> tuple[float, float]:
        if not card.state.is_hovered or max_tilt <= 0.0:
            return 0.0, 0.0

        mouse = rl.get_mouse_position()
        nx = max(-1.0, min(1.0, (mouse.x - (card.center.x - width / 2)) / width * 2.0 - 1.0))
        ny = max(-1.0, min(1.0, (mouse.y - (card.center.y - height / 2)) / height * 2.0 - 1.0))
        return -nx * max_tilt, ny * max_tilt

    def _update_state(self, card: BaseCard, style: CardStyle, width: float, height: float) -> _CardAnimState | None:
        key = id(card)
        state = self._states.get(key)

        if state is None and self._mode_for(card) == CardVisualMode.NORMAL:
            return None

        if state is None:
            state = _CardAnimState()
            self._states[key] = state

        target_y, target_x = self._target_tilt(card, width, height, style.max_tilt)
        blend = min(1.0, rl.get_frame_time() * 12.0)

        state.tilt_y += (target_y - state.tilt_y) * blend
        state.tilt_x += (target_x - state.tilt_x) * blend
        state.glow_width += (style.glow_width - state.glow_width) * blend
        state.glow_alpha += (style.glow_alpha - state.glow_alpha) * blend
        state.inset += (style.inset - state.inset) * blend

        if state.is_idle and self._mode_for(card) == CardVisualMode.NORMAL:
            self._states.pop(key, None)
            return None

        return state

    def _set_uniform(self, name: str, values: list[float], uniform_type: int) -> None:
        if uniform_type == rl.ShaderUniformDataType.SHADER_UNIFORM_FLOAT:
            value_ptr = rl.ffi.new("float *", values[0])
        else:
            value_ptr = rl.ffi.new(f"float[{len(values)}]", values)
        rl.set_shader_value(self.shader, self._locations[name], value_ptr, uniform_type)

    def draw(self, card: BaseCard) -> None:
        render_texture = card.render_texture
        texture = render_texture.texture if render_texture is not None else card.back_tex
        if texture is None:
            return

        width = texture.width * card.scale
        height = texture.height * card.scale
        style = CARD_STYLES[self._mode_for(card)]
        anim = self._update_state(card, style, width, height)

        if anim is not None:
            glow = getattr(card, "bg_color", rl.Color(235, 220, 185, 255))
            self._set_uniform(
                "glowColor",
                [glow.r / 255.0, glow.g / 255.0, glow.b / 255.0, anim.glow_alpha],
                rl.ShaderUniformDataType.SHADER_UNIFORM_VEC4,
            )
            self._set_uniform("glowWidth", [anim.glow_width], rl.ShaderUniformDataType.SHADER_UNIFORM_FLOAT)
            self._set_uniform(
                "textureSize", [float(texture.width), float(texture.height)],
                rl.ShaderUniformDataType.SHADER_UNIFORM_VEC2,
            )
            self._set_uniform("y_rot", [anim.tilt_y], rl.ShaderUniformDataType.SHADER_UNIFORM_FLOAT)
            self._set_uniform("x_rot", [anim.tilt_x], rl.ShaderUniformDataType.SHADER_UNIFORM_FLOAT)
            # FOV ridotto a 20.0 per rendere la prospettiva 3D molto più raffinata e sottile
            self._set_uniform("fov", [20.0], rl.ShaderUniformDataType.SHADER_UNIFORM_FLOAT)
            self._set_uniform("inset", [anim.inset], rl.ShaderUniformDataType.SHADER_UNIFORM_FLOAT)
            self._set_uniform(
                "cardCenter", [float(card.center.x), float(card.center.y)],
                rl.ShaderUniformDataType.SHADER_UNIFORM_VEC2,
            )
            self._set_uniform(
                "cardSize", [float(width), float(height)],
                rl.ShaderUniformDataType.SHADER_UNIFORM_VEC2,
            )
            rl.begin_shader_mode(self.shader)

        rl.draw_texture_pro(
            texture,
            rl.Rectangle(0, 0, texture.width, -texture.height if render_texture is not None else texture.height),
            rl.Rectangle(int(card.center.x), int(card.center.y), int(width), int(height)),
            rl.Vector2(width / 2, height / 2),
            card.rotation,
            rl.WHITE,
        )

        if anim is not None:
            rl.end_shader_mode()

import pyray as rl

from shaders.card_visuals import CardVisualRenderer


class Shaders:
    glow_shader: rl.Shader
    card_visuals: CardVisualRenderer

    @classmethod
    def init(cls):
        cls.glow_shader = rl.load_shader("shaders/glow.vs", "shaders/glow.fs")
        cls.card_visuals = CardVisualRenderer(cls.glow_shader)

    @classmethod
    def unload(cls) -> None:
        if hasattr(cls, "glow_shader"):
            rl.unload_shader(cls.glow_shader)

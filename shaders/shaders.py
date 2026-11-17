import pyray as rl


class Shaders:
    glow_shader: rl.Shader

    @classmethod
    def init(cls):
        # Load it once
        cls.glow_shader = rl.load_shader("shaders/glow.vs", "shaders/glow.fs")
        # glow_color_loc = rl.get_shader_location(glow_shader, "glowColor")
        # glow_width_loc = rl.get_shader_location(glow_shader, "glowWidth")
        # texture_size_loc = rl.get_shader_location(glow_shader, "textureSize")
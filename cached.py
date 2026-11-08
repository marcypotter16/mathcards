import pyray as rl

class Cache:
    card_back: rl.Texture | None = None

    @classmethod
    def init(cls) -> None:
        """To be called after window initialization"""
        cls.card_back = rl.load_texture("assets/backs/orbit.png")
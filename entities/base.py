from pyray import RenderTexture


class Entity:
    def __init__(self) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def render(self, logical_texture: RenderTexture | None) -> None:
        pass
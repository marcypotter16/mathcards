from entities.base import Entity
import pyray as rl

class UIButton(Entity):
    def __init__(self, text: str, rect: rl.Rectangle, font: rl.Font, color: rl.Color):
        self.text = text
        self.rect = rect
        self.font = font
        self.color = color
        
        self.is_hovered = False
        self.is_clicked = False

    def update(self, dt: float) -> None:
        mouse_pos = rl.get_mouse_position()
        self.is_hovered = rl.check_collision_point_rec(mouse_pos, self.rect)
        self.is_clicked = self.is_hovered and rl.is_mouse_button_released(rl.MouseButton.MOUSE_BUTTON_LEFT)

    def render(self, logical_texture: rl.RenderTexture | None = None) -> None:
        # Lighten the color if hovered
        draw_color = self.color
        if self.is_hovered:
            # Verifica se ha l'attributo .r (caso struct C/Raylib)
            if hasattr(self.color, 'r'):
                r, g, b, a = self.color.r, self.color.g, self.color.b, self.color.a
            else:
                # Caso tupla/lista standard di Python
                r, g, b, a = self.color

            if self.is_hovered:
                draw_color = rl.Color(min(255, r + 40), min(255, g + 40), min(255, b + 40), 255)
            else:
                draw_color = self.color # it's already a tuple, so it works
            draw_color = rl.Color(
                min(255, r + 40),
                min(255, g + 40),
                min(255, b + 40),
                255
            )

        rl.draw_rectangle_rounded(self.rect, 0.2, 4, draw_color)
        
        # Center the text automatically
        text_size = rl.measure_text_ex(self.font, self.text, 24, 1.0)
        text_pos = (
            self.rect.x + (self.rect.width - text_size.x) / 2,
            self.rect.y + (self.rect.height - text_size.y) / 2
        )
        rl.draw_text_ex(self.font, self.text, text_pos, 24, 1.0, rl.WHITE)
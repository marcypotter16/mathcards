import pyray as rl
from entities.base import Entity
from dataclasses import dataclass

@dataclass
class LogMessage:
    text: str
    duration: float
    time_left: float
    color: rl.Color

class _Printer(Entity):
    def __init__(self) -> None:
        super().__init__()
        self.messages: list[LogMessage] = []
        self.max_messages = 8
        self.font_size = 20
        self.spacing = 1.0
        self.font: rl.Font | None = None
        self.anchor_x = 20
        self.anchor_y = 20
        self.line_height = 26

    def init(self, font: rl.Font) -> None:
        """Call this in main.py after loading the font."""
        self.font = font

    def print(self, *args, duration: float = 4.0, color: rl.Color = rl.WHITE) -> None:
        """Mimics Python's print(), but outputs to the screen."""
        text = " ".join(str(arg) for arg in args)
        msg = LogMessage(text, duration, duration, color)
        self.messages.append(msg)

        # Keep list bounded
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

    def update(self, dt: float) -> None:
        for msg in self.messages:
            msg.time_left -= dt
        
        # Remove expired messages
        self.messages = [m for m in self.messages if m.time_left > 0]

    def render(self, logical_texture: rl.RenderTexture | None = None) -> None:
        if not self.messages:
            return

        font = self.font if self.font else rl.get_font_default()
        
        y = self.anchor_y
        for msg in self.messages:
            # Fade out in the last 1 second
            alpha = min(1.0, msg.time_left)
            
            # Pseudo-shadow for readability against any background
            shadow_color = rl.Color(0, 0, 0, int(180 * alpha))
            # print(msg.color, type(msg.color))
            main_color = rl.Color(msg.color[0], msg.color[1], msg.color[2], int(255 * alpha)) # type: ignore

            # Draw shadow (offset by 2px)
            rl.draw_text_ex(font, msg.text, rl.Vector2(self.anchor_x + 2, y + 2), self.font_size, self.spacing, shadow_color)
            
            # Draw main text
            rl.draw_text_ex(font, msg.text, rl.Vector2(self.anchor_x, y), self.font_size, self.spacing, main_color)
            
            y += self.line_height

# The global singleton instance
Printer = _Printer()
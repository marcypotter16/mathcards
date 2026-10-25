from asyncio import wrap_future
from sys import exit

from GameEntities.Card import Card
import pyray as rl

from Vector import Vector2
from typst_formula_renderer import FormulaResult, TypstFormulaRenderer

class FormulaCard(Card):
    def __init__(self, formula: str) -> None:
        super().__init__(_dont_initialize_render_texture=True)
        self.width, self.height                                 = 225, 150
        self.dimensions                                         = Vector2(self.width, self.height)
        self.render_texture                                     = rl.load_render_texture(self.width, self.height)
        self.formula                                            = formula
        self.formula_name:          str
        self.tfr:                   TypstFormulaRenderer        = TypstFormulaRenderer(padding_pt=6)
        self.formula_texture:       rl.Texture
        # Keep only synchronous setup here

    @classmethod
    async def create(cls, formula: str, formula_name="placeholder"):
        # 1. Instantiate the object synchronously
        instance = cls(formula)
        instance.formula_name = formula_name
        
        # 2. Perform your async work
        ff = instance.tfr.queue_formula(formula_name, formula, 250)
        fr: FormulaResult = await wrap_future(ff)
        
        if not fr.success:
            print(fr.stderr)
            exit(1)
            
        instance.formula_texture = rl.load_texture(str(fr.png_path.resolve()))
        rl.set_texture_filter(instance.formula_texture, rl.TextureFilter.TEXTURE_FILTER_TRILINEAR)
        
        # 3. Return the fully initialized instance
        return instance


    def bake_texture(self):
        """Renders the card's internal graphics onto its own texture."""
        rl.begin_texture_mode(self.render_texture)
        rl.clear_background(rl.BLANK)
        bt = self.border_thickness
        # outline
        rl.draw_rectangle_rounded(
            rl.Rectangle( 0, 0, self.width, self.height ), 
            .1, 
            0, 
            self.border_color)
        rl.draw_rectangle_rounded(
            rl.Rectangle( bt * .5, bt * .5, self.width - bt, self.height - bt ), 
            .1, 
            4, 
            self.bg_color)        
        rl.end_texture_mode()
        self.texture_is_dirty = False

    def update(self, dt):
        if self._is_snapping_back:
            self.tm.update(dt)
            return
        mouse = Vector2.from_raylib(rl.get_mouse_position())
    
        # 5. Process continuous physics/movement based on states
        if self.state.is_dragged:
            self.center = Vector2.from_raylib(rl.vector2_lerp(self.center.raylib_ref, mouse.raylib_ref, 22.0 * dt))
    
        # 6. Process Visual Tweens from triggers
        if self.state.started_hovering:
            self.texture_is_dirty = True
            self.tween_scale(self.scale_when_hovered)
            self.tween_center(self.get_center_after_hover())
        elif self.state.ended_hovering:
            self.texture_is_dirty = True
            self.tween_center(self.center_rest)
            self.tween_scale(1.0)
    
        if self.state.started_dragging:
            self.center_before_drag = Vector2(self.center_rest.x, self.center_rest.y)
            self.tween_rotation(self.rot_when_hovered)
        elif self.state.ended_dragging:
            self._is_snapping_back = True
            self.snap_back()
            self.tween_rotation(0.0)
    
        # 7. Engine & Data updates
        self.tm.update(dt)
    
        self._timer += dt

    def render(self, logical_texture: rl.RenderTexture):
        # 1. Update/bake textures if dirty
        if self.texture_is_dirty:
            self.bake_texture()  # Bake background and formula independently
            rl.begin_texture_mode(logical_texture)

        # 2. Draw the card background texture (using your existing scale/rotation logic)
        rl.draw_texture_pro(
            self.render_texture.texture,
            rl.Rectangle(0, 0, self.width, -self.height),
            rl.Rectangle(
                self.center._x,
                self.center._y,
                self.width * self.scale,
                self.height * self.scale,
            ),
            rl.Vector2(
                (self.width * self.scale) / 2, (self.height * self.scale) / 2
            ),
            self.rotation,
            rl.WHITE,
        )

        # 3. Draw the formula texture on top
        # If the formula is positioned relative to the card's center, 
        # scale its local offset by self.scale so it expands outward cleanly from the center!
        if self.formula is not None:

            # Draw the formula texture with its own crisp scaling/rotation
            # Note: Raylib's draw_texture_pro handles rotation around an origin nicely.
            fw, fh = self.formula_texture.width, self.formula_texture.height
            formula_dest = rl.Rectangle(
                self.center._x,
                self.center._y,
                fw * self.scale,
                fh * self.scale,
            )

            rl.draw_texture_pro(
                self.formula_texture,
                rl.Rectangle(
                    0, 0, fw, fh
                ),  # source
                formula_dest,  # destination
                rl.Vector2(formula_dest.width / 2, formula_dest.height / 2),  # origin
                self.rotation,  # same rotation as the card
                rl.BLACK,
            )

    def __repr__(self) -> str:
        return f"Formula {self.formula_name}: {self.formula}"
    
from entities.base import Entity
import pyray as rl

from Settings import FONT_PATH

show_message = True
slider_value = 0.0
checkbox_state = False
class GameUI(Entity):
    def __init__(self) -> None:
        super().__init__()
        self.font:      rl.Font     = rl.load_font_ex(FONT_PATH, 24, None, 0)
        rl.gui_set_font(self.font)
        rl.gui_set_style(rl.GuiControl.DEFAULT, rl.GuiDefaultProperty.TEXT_SIZE, 24)

    def render(self) -> None:
        global show_message, slider_value, checkbox_state
        rl.gui_label(rl.Rectangle(40, 40, 600, 40), "Pannello di Controllo UI")

        # 2. Pulsante (Button)
        # Ritorna True nel frame esatto in cui viene cliccato
        if rl.gui_button(rl.Rectangle(40, 80, 120, 30), "Cliccami"):
            show_message = not show_message

        # 3. Slider (SliderBar)
        # Richiede l'uso di puntatori CFFI per tracciare la modifica del valore
        # Sintassi: gui_slider_bar(rect, testo_sinistra, testo_destra, valore, min, max)
        slider_ptr = rl.ffi.new("float *", slider_value)
        rl.gui_slider_bar(rl.Rectangle(40, 130, 200, 20), "Min", f"{slider_value:.2f}", slider_ptr, 0.0, 1.0)
        slider_value = slider_ptr[0]  # Recupera il valore aggiornato dal puntatore

        # 4. Casella di controllo (CheckBox)
        # Anch'essa richiede un puntatore booleano per aggiornare lo stato in tempo reale
        bool_ptr = rl.ffi.new("bool *", checkbox_state)
        rl.gui_check_box(rl.Rectangle(40, 170, 20, 20), "Attiva Modalita'", bool_ptr)
        checkbox_state = bool_ptr[0]

        # Mostra un messaggio condizionale in base al pulsante
        if show_message:
            rl.gui_label(rl.Rectangle(40, 220, 300, 20), "Stato: Pulsante Attivato!")

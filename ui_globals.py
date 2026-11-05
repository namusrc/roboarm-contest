from textual.binding import BindingType

MAIN_FOOTER_BINDINGS: list[BindingType] = [
        ('h', 'switch_screen(\'home\')', 'Home'),
        ('c', 'switch_screen(\'console\')', 'Console'),
        ('m', 'menu_controller', 'Controller'),
        ('q', 'quit', 'Quit'),
]

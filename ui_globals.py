from textual.binding import BindingType

MAIN_FOOTER_BINDINGS: list[BindingType] = [
        ('h', 'app.switch_screen(\'home\')', 'Home'),
        ('c', 'app.switch_screen(\'console\')', 'Console'),
        ('m', 'app.switch_screen(\'controller\')', 'Controller'),
        ('q', 'quit', 'Quit'),
]

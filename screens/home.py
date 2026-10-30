from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Header, Footer, Placeholder

import ui_globals

class WidthAuto(Placeholder):
    DEFAULT_CSS = """
    WidthAuto {
        width: 1fr;
    }
    """

class Home(Screen):    
    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield WidthAuto()
            yield WidthAuto()
        with Horizontal():
            yield WidthAuto()
            yield WidthAuto()
        yield Footer()

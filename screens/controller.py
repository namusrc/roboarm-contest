from textual import events
from textual.binding import Binding
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.containers import Container, Grid, Horizontal, Vertical
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Button, DataTable, Header, Footer, Label, Placeholder, Rule, Static

import ui_globals

from modules.logger import logger
from widgets.RawSensorReading import RawSensorReading

class Controller(Screen):
    DEFAULT_CSS = """
    
    LogWidget {
        height: 2fr
    }

    Button {
        width: 100%;
        height: 100%;
    }
    """

    BINDINGS = [
        ('escape', 'app.switch_screen(\'home\')', 'Home'),
        ('q', 'quit', 'Quit'),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            with Horizontal():
                with Vertical():
                    yield Button()
                    yield Button()
                    yield Placeholder()
                with Vertical():
                    yield Button()
                    yield Button()
            with Horizontal():
                with Vertical():
                    yield Button()
                    yield Button()
                with Vertical():
                    yield Button()
                    yield Button()
        yield Footer()

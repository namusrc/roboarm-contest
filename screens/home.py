from textual.reactive import reactive
from textual.app import ComposeResult
from textual.containers import Container, Grid, Horizontal, Vertical
from textual.screen import Screen
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import DataTable, Header, Footer, Label, Placeholder, Rule, Static

import ui_globals

from modules.logger import logger

from widgets.RawSensorReading import RawSensorReading
from widgets.LogWidget import LogWidget
from widgets.CommandInput import CommandInput

class Home(Screen):
    DEFAULT_CSS = """
    
    LogWidget {
        height: 2fr
    }
    """
    BINDINGS = ui_globals.MAIN_FOOTER_BINDINGS + [Binding("i", "input_focus", "Focus", show=False)]

    def action_input_focus(self) -> None:
        self.query_one(CommandInput).focus()

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield RawSensorReading()
            yield LogWidget()
            yield CommandInput()
        yield Footer()

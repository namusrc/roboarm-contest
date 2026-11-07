from textual import events
from textual.binding import Binding
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.containers import Container, Grid, Horizontal, Vertical
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import DataTable, Header, Footer, Label, Placeholder, Rule, Static

from screens.console import LogWidget
import ui_globals

from modules.logger import logger
from widgets.RawSensorReading import RawSensorReading

class Controller(Screen):
    DEFAULT_CSS = """
    
    LogWidget {
        height: 2fr
    }
    """

    BINDINGS = [
        ('escape', 'app.switch_screen(\'home\')', 'Home'),
        ('q', 'quit', 'Quit'),
        # Movement Keys
    ]

    def action_move(self, joint_id: int, sign: int)

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield RawSensorReading()
            yield Label("")
        yield Footer()

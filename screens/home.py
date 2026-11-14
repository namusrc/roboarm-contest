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

class Home(Screen):
    DEFAULT_CSS = """
    
    LogWidget {
        height: 2fr
    }
    """
    BINDINGS = ui_globals.MAIN_FOOTER_BINDINGS

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield RawSensorReading()
            yield LogWidget()
        yield Footer()

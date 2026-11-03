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

class SizeAuto(Placeholder):
    DEFAULT_CSS = """
    SizeAuto {
        height: 1fr;
        width: 1fr;
    }
    """

class AngleViewer(Placeholder):
    DEFAULT_CSS = """
    AngleViewer {
        height: 0.3fr;
        width: 1fr;
    }
    """
class Home(Screen):
    DEFAULT_CSS = """
    
    LogWidget {
        height: 2fr
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical():
                yield LogWidget()
            with Vertical():
                yield RawSensorReading()
                yield AngleViewer()
                with Horizontal():
                    yield SizeAuto()
                    yield SizeAuto()
                    yield SizeAuto()
        yield Footer()

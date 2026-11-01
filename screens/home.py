from textual.app import ComposeResult
from textual.containers import Container, Grid, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Header, Footer, Placeholder, Rule

from screens.console import LogWidget
import ui_globals

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
                yield SizeAuto()
                yield LogWidget()
            with Vertical():
                yield SizeAuto()
                yield AngleViewer()
                yield SizeAuto()
        yield Footer()

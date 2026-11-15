from textual.reactive import reactive
from textual.app import ComposeResult
from textual.containers import Container, Grid, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import Button, DataTable, Header, Footer, Label, Placeholder, Rule, Static

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

    VerticalScroll {
        width: 16;
        scrollbar-visibility: hidden;
    }
    """
    BINDINGS = ui_globals.MAIN_FOOTER_BINDINGS + [Binding("i", "input_focus", "Focus", show=False)]

    def action_input_focus(self) -> None:
        self.query_one(CommandInput).focus()

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield RawSensorReading()
            with Horizontal():
                with Vertical(classes="command"):
                    yield LogWidget()
                    yield CommandInput()
                with VerticalScroll():
                    yield Label("Pickups")
                    yield Button("Pickup Left")
                    yield Button("Pickup Right")
                    yield Button("Pickup Middle")
                with VerticalScroll():
                    yield Label("Flicks")
                    yield Button("Flick Left")
                    yield Button("Flick Right")
                    yield Button("Flick Middle")
                with VerticalScroll():
                    yield Label("Full Seq.")
                    yield Button("Flick")
                    yield Button("Pickup")
                    yield Label("Waypoints")
                    yield Button("Home")
                with VerticalScroll():
                    yield Label("Gripper")
                    yield Button("Open")
                    yield Button("Close")
                    yield Button("Push")
                    yield Label("Worker")
                    yield Button("Pause")
        yield Footer()

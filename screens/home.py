from typing import Literal

from textual.reactive import reactive
from textual.app import ComposeResult
from textual.containers import Container, Grid, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import Button, DataTable, Header, Footer, Label, Placeholder, Rule, Static

from modules import shell
import ui_globals

from modules.logger import logger

from widgets.RawSensorReading import RawSensorReading
from widgets.LogWidget import LogWidget
from widgets.CommandInput import CommandInput

class GripperButton(Button):
    def __init__(self, btnType: Literal["open", "close", "push"]):
        super().__init__(btnType.capitalize())

        self.btnType = btnType

    def on_button_pressed(self):
        shell.shell.do_gripper(self.btnType)

class SequenceButton(Button):
    def __init__(self, btnType: Literal["flick", "pickup"]):
        super().__init__(btnType.capitalize())

        self.btnType = btnType
        
    def on_button_pressed(self):
        match self.btnType:
            case "flick":
                shell.shell.do_sequence("load flick_new_v2")
            case "pickup":
                pass

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
                    yield SequenceButton("flick")
                    yield SequenceButton("pickup")

                    yield Label("Waypoints")
                    yield Button("Home")
                with VerticalScroll():
                    yield Label("Gripper")
                    yield GripperButton("open")
                    yield GripperButton("close")
                    yield GripperButton("push")

                    yield Label("Worker")
                    yield Button("Pause")
        yield Footer()

from textual.reactive import reactive
from textual.app import ComposeResult
from textual.containers import Container, Grid, Horizontal, Vertical
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import DataTable, Header, Footer, Label, Placeholder, Rule, Static

from screens.console import LogWidget
import ui_globals

from modules.logger import logger

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

class RawSensorReading(Container):
    DEFAULT_CSS="""
    RawSensorReading Label {
        padding-left: 1;
        width: 100%;
    }

    RawSensorReading .entry {
        content-align-vertical: middle;
        height: 1fr;
    }
    RawSensorReading .header {
        background: red 20%;
    }
    """

    _motor_names = ("Base", "Shoulder", "Elbow", "Wrist", "Gripper")
    raw_readings: reactive[list[float]] = reactive([0, 0, 0, 0, 0], init=True)

    def on_mount(self) -> None:
        pass

    def watch_raw_readings(self) -> None:
        labels = self.query(Label)
        readings = self.raw_readings
        for label in labels:
            if label.id is None:
                continue
            labeltype, index = label.id.split("_")
            try:
                reading = readings[int(index)]
                if labeltype == "rawreading":
                    label.update(f"{reading:.2f}")
                elif labeltype == "angle":
                    label.update(f"{(reading/4095*360):.2f}deg")
            except IndexError:
                logger.error(f"Failed to index for motor reading. Index: {index}")
            except:
                logger.error("Unhandled exception error.")

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical():
                yield Label("Motor ID", classes="header")
                for i in range(len(self._motor_names)):
                    # yield RobotInfo()
                    yield Label(f"Motor {i + 1}", classes="entry")
            with Vertical():
                yield Label("Motor Name", classes="header")
                for name in self._motor_names:
                    yield Label(name, classes="entry")
            with Vertical():
                yield Label("Raw Reading", classes="header")
                for i in range(5):
                    yield Label(str(i), id=f"rawreading_{i}", classes="entry")
            with Vertical():
                yield Label("Angle (deg)", classes="header")
                for i in range(5):
                    yield Label(str(i), id=f"angle_{i}", classes="entry")

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

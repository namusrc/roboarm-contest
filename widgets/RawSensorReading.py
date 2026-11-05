from textual.reactive import reactive
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label

from modules.logger import logger
from modules.settings_loader import default_settings
import modules.arm_controller as arm

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

    def on_mount(self) -> None:
        self.set_interval(0.1, self.update_raw_readings)

    def update_raw_readings(self) -> None:
        labels = self.query(Label)
        readings = arm.controller.worker_thread.servo_positions 

        if readings is None:
            return

        for label in labels:
            if label.id is None:
                continue
            labeltype, index = label.id.split("_")
            try:
                joint = next(j for j in default_settings.servo.joints if j.id == int(index))
                reading = readings[joint.name]
                if labeltype == "rawreading":
                    label.update(f"{reading.raw}")
                elif labeltype == "angle":
                    label.update(f"{reading.angle:.2f}deg")
            except IndexError:
                logger.error(f"Failed to index for motor reading. Index: {index}")
            except Exception as err:
                logger.error(f"Unhandled exception error: {err}")

    def compose(self) -> ComposeResult:
        joints = default_settings.servo.joints
        motor_count = len(joints)

        with Horizontal():
            with Vertical():
                yield Label("Motor ID", classes="header")
                for i  in range(motor_count):
                    # yield RobotInfo()
                    yield Label(f"Motor {i + 1}", classes="entry")
            with Vertical():
                yield Label("Motor Name", classes="header")
                for joint in joints:
                    yield Label(joint.name, classes="entry")
            with Vertical():
                yield Label("Raw Reading", classes="header")
                for joint in joints:
                    yield Label("0", id=f"rawreading_{joint.id}", classes="entry")
            with Vertical():
                yield Label("Angle (deg)", classes="header")
                for joint in joints:
                    yield Label("0.00deg", id=f"angle_{joint.id}", classes="entry")

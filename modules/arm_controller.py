from dataclasses import dataclass
import threading

from modules.scservo_sdk.port_handler import PortHandler
from modules.settings_loader import JointSettings, Settings, default_settings
from modules.scservo_sdk.sms_sts import sms_sts

import modules.arm_helpers as arm 
from logger import logger

class Worker(threading.Thread):
    frequency = 1
    servo_positions: dict[str, ArmPosition] | None = None
    def __init__(self, event, frequency = 1):
        super().__init__()
        self.stopped = event
        self.frequency = frequency
    def run(self):
        # Loop over self.frequency times on a separate thread
        while not self.stopped.wait(1/self.frequency):
            self.servo_positions = controller.get_pos_all()

# Arm positions helpers
@dataclass
class ArmPosition:
    raw: int
    angle: float

def format_raw_pos(rawpos: dict) -> dict[str, ArmPosition]:
    return { name: ArmPosition(reading, arm.position_to_angle(name, reading)) for name, reading in rawpos.items() }

class Controller:
    settings: Settings

    port: PortHandler | None
    packet_handler: sms_sts | None

    worker_event: threading.Event
    worker_thread: Worker 
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or default_settings
        self.port = None
        self.packet_handler = None

        self.worker_event = threading.Event()
        self.worker_thread = Worker(self.worker_event) 
    def connect(self) -> sms_sts | None:
        connection = self.settings.connection
        logger.info(f"Attempting to connect to: {connection.serial_port} at a BAUD rate of {connection.baud_rate}")
        port = None
        try:
            port, packet_handler = arm.connect()
            self.packet_handler = packet_handler
            self.port = port

            logger.info("Connection successful. Disabling torque.")
            arm.disable_all_torque(packet_handler)

            self.worker_thread.start()

            return packet_handler 
        except Exception as err:
            logger.error(f"Failed to connect to serial port. Error was raised: {err}")

    def get_pos_all(self):
        if not self.packet_handler:
            raise RuntimeError("Undefined packet handler")

        raw = arm.read_all(self.packet_handler)
        return format_raw_pos(raw)

    def start_worker(self) -> None:
        if not self.worker_event.is_set():
            return
        
        self.worker_thread.start()
    def quit_worker(self) -> None:
        if self.worker_event.is_set():
            return
        
        self.worker_event.set()

controller = Controller()

import threading

from modules.scservo_sdk.port_handler import PortHandler
from modules.settings_loader import Settings, default_settings
from modules.scservo_sdk.sms_sts import sms_sts

import modules.arm_helpers as arm 
from logger import logger

class Worker(threading.Thread):
    frequency = 1
    servo_positions = []
    def __init__(self, event, frequency = 1):
        super().__init__()
        self.stopped = event
        self.frequency = frequency
    def run(self):
        while not self.stopped.wait(1/self.frequency):
            logger.debug("Worker Running")

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

    def get_pos_all(self) -> dict:
        if not self.packet_handler:
            raise RuntimeError("Undefined packet handler")
        return arm.read_all(self.packet_handler)

    def start_worker(self) -> None:
        if not self.worker_event.is_set():
            return
        
        self.worker_thread.start()
    def quit_worker(self) -> None:
        if self.worker_event.is_set():
            return
        
        self.worker_event.set()

controller = Controller()

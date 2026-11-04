import threading

from modules.scservo_sdk.port_handler import PortHandler
from modules.settings_loader import Settings, default_settings
from modules.scservo_sdk.sms_sts import sms_sts

import modules.arm_helpers as arm 
from logger import logger

class Worker(threading.Thread):
    frequency = 1
    servo_positions = []
    def __init__(self, event, frequency = 10):
        self.stopped = event
        self.frequency = frequency
    def run(self):
        while not self.stopped.wait(1/self.frequency):
            logger.debug("Worker Running")

class Controller:
    settings: Settings
    port: PortHandler | None
    packet_handler: sms_sts | None
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or default_settings
        self.port = None
        self.packet_handler = None
    
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

            return packet_handler 
        except Exception as err:
            logger.error(f"Failed to connect to serial port. Error was raised: {err}")

controller = Controller()

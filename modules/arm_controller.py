from dataclasses import dataclass
import threading

from modules.scservo_sdk.port_handler import PortHandler
from modules.settings_loader import JointSettings, Settings, default_settings
from modules.scservo_sdk.sms_sts import sms_sts

import modules.arm_helpers as arm 
from logger import logger

from collections import deque

@dataclass
class MoveInstructionSingle:
    joint: JointSettings 
    rawpos: int
    speed: int = default_settings.servo.configs["move_speed"]
    acceleration: int = default_settings.servo.configs["move_acceleration"]
@dataclass
class MoveInstructionMultiple:
    joints: list[JointSettings]
    rawpositions: list[int]

class Worker(threading.Thread):
    frequency = 1
    def __init__(self, event, frequency = 1):
        super().__init__()
        self.stopped = event
        self.frequency = frequency
        self.move_queue: deque[MoveInstructionSingle | MoveInstructionMultiple] = deque()

    def run(self):
        # Loop over self.frequency times on a separate thread
        while not self.stopped.wait(1/self.frequency):
            try:
                if self.move_queue:
                    move = self.move_queue.pop()

                    try: 
                        if isinstance(move, MoveInstructionSingle):
                            controller.move_joint(move)
                        elif isinstance(move, MoveInstructionMultiple):
                            pass
                    except Exception as err:
                        logger.error(f"An error has occurred when running the move_qeue: {err}")

                controller.get_pos_all()
            except Exception as err:
                logger.error(f"An error has occured in the worker thread: {err}")
            

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

    servo_positions: dict[str, ArmPosition] | None = None
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or default_settings
        self.port = None
        self.packet_handler = None

        self.worker_event = threading.Event()
        self.worker_thread = Worker(self.worker_event, frequency=default_settings.global_poll_rate) 
    def connect(self) -> sms_sts | None:
        if self.port is not None and self.port.is_open:
            logger.warning("Serial port is already open. Use reconnect to reset the connection.")
            return self.packet_handler

        if self.worker_event.is_set() or self.worker_thread.ident is not None:
            self.worker_event = threading.Event()
            self.worker_thread = Worker(
                self.worker_event,
                frequency=self.settings.global_poll_rate,
            )

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
            if port is not None and port.is_open:
                port.closePort()
            self.port = None
            self.packet_handler = None
            return None

    def reconnect(self) -> sms_sts | None:
        self.quit_worker()
        return self.connect()

    def move_joint(self, move: MoveInstructionSingle):
        if not self.packet_handler:
            raise RuntimeError("Undefined packet handler")

        rawpos = move.rawpos
        limits = move.joint.raw_position_limits
        if limits is not None:
            rawpos = min(max(rawpos, limits[0]), limits[1])
            if rawpos != move.rawpos:
                logger.warning(
                    f"Clamping {move.joint.name} position from {move.rawpos} to {rawpos}."
                )

        if not 0 <= rawpos <= 4095:
            raise ValueError("Raw servo position must be between 0 and 4095")

        result, error = self.packet_handler.write1ByteTxRx(
            move.joint.id,
            arm.SMS_STS_TORQUE_ENABLE,
            1,
        )
        arm.check_result(
            self.packet_handler,
            result,
            error,
            f"Enable torque for {move.joint.name}",
        )

        result, error = self.packet_handler.RegWritePosEx(
            move.joint.id,
            rawpos,
            move.speed,
            move.acceleration,
        )
        arm.check_result(
            self.packet_handler,
            result,
            error,
            f"Register move for {move.joint.name}",
        )

        result = self.packet_handler.RegAction()
        arm.check_result(
            self.packet_handler,
            result,
            0,
            f"Start move for {move.joint.name}",
        )
        logger.info(f"Move sent to {move.joint.name} (ID {move.joint.id}) at position {rawpos}.")

    def disable_torque(self) -> None:
        if not self.packet_handler:
            raise RuntimeError("Undefined packet handler")

        arm.disable_all_torque(self.packet_handler)

    def get_pos_all(self):
        if not self.packet_handler:
            raise RuntimeError("Undefined packet handler")

        raw = arm.read_all(self.packet_handler)
        self.servo_positions = format_raw_pos(raw)
        return self.servo_positions

    def start_worker(self) -> None:
        if not self.worker_event.is_set():
            return
        
        self.worker_thread.start()
    def quit_worker(self) -> None:
        self.worker_event.set()
        if self.worker_thread.is_alive():
            self.worker_thread.join()

        try:
            if self.packet_handler is not None:
                arm.disable_all_torque(self.packet_handler)
        except Exception as err:
            logger.error(f"Failed to disable servo torque during shutdown: {err}")
        finally:
            if self.port is not None and self.port.is_open:
                self.port.closePort()
        self.port = None
        self.packet_handler = None
        self.servo_positions = None

controller = Controller()

from dataclasses import dataclass
import threading

from modules.scservo_sdk.port_handler import PortHandler
from modules.settings_loader import JointSettings, Settings, default_settings
from modules.scservo_sdk.sms_sts import sms_sts

import modules.arm_helpers as arm 
from logger import logger

from collections import deque

from abc import ABC, abstractmethod

MAX_TICKS = default_settings.servo.configs["ticks_per_revolution"] or 4096

# Helper function, move elsewhere later plz
def within(value: float, target: float, threshold: int):
    return (value <= (target + threshold)) and (value >= (target - threshold))
def sign(value: float):
    if value == 0:
        return value
    return -1 if value < 0  else 1

class WorkerInstruction(ABC):
    def __init__(self) -> None:
        super().__init__()

        self.finished = False

    @abstractmethod
    def run(self) -> None:
        if (controller.packet_handler and controller.port) is None:
            self.finished = True
            raise RuntimeError("No connection found")

class MoveSingleJoint(WorkerInstruction):
    def __init__(self, joint: JointSettings, rawpos: int, speed: int | None, accel: int | None) -> None:
        super().__init__()

        self.joint = joint
        self.rawpos = rawpos
        self.speed = speed or default_settings.servo.configs["move_speed"]
        self.accel = accel or default_settings.servo.configs["move_acceleration"]

        self.set_direction = False

    def run(self) -> None:
        super().run()
        if controller.servo_readings is None:
            # Give up and quit if there's no servo readings LMFAO
            self.finished = True
            raise RuntimeError("Servo readings required.")

        readings = controller.servo_readings[self.joint.name]
        curpos = readings.rawpos
        rawpos = self.rawpos % MAX_TICKS

        delta = (rawpos - curpos + 3/2*MAX_TICKS) % MAX_TICKS - MAX_TICKS/2 
        dist = abs(delta)

        if not self.set_direction:
            # Stolen from https://math.stackexchange.com/questions/1649841/signed-angle-difference-without-conditions/1649850#1649850
            self.speed *= sign(delta)
            self.set_direction = True

        # TODO: Current logic can completely overshoot the target position, maybe a dynamic solution involving the speed?
        # For funny result try running at default speed (3000)
        if dist <= self.speed or sign(self.speed) != sign(delta):
            controller.joint_set_speed(self.joint.id, 0, self.accel)
            self.finished = True
            return
        
        controller.joint_set_speed(self.joint.id, round(self.speed), self.accel)

class DisableTorque(WorkerInstruction):
    def __init__(self) -> None:
        super().__init__()

    def run(self) -> None:
        super().run()
        controller.disable_torque()
        self.finished = True

class Worker(threading.Thread):
    frequency = 1
    def __init__(self, event, frequency = 1):
        super().__init__()
        self.stopped = event
        self.frequency = frequency
        self.inst_queue: deque[WorkerInstruction] = deque()

        self.current_instruction: WorkerInstruction | None = None

    def run(self):
        # Loop over self.frequency times on a separate thread
        while not self.stopped.wait(1/self.frequency):
            try:
                if self.current_instruction and not self.current_instruction.finished:
                    self.current_instruction.run()
                elif self.inst_queue:
                    inst = self.inst_queue.pop()
                    self.current_instruction = inst

                    try: 
                        pass
                    except Exception as err:
                        logger.error(f"An error has occurred when running the move_qeue: {err}")

                controller.get_pos_speed_all()
            except Exception as err:
                logger.error(f"An error has occured in the worker thread: {err}")
            

# Arm positions helpers
@dataclass
class ArmPosition:
    raw: int
    angle: float

def format_raw_pos(rawpos: dict) -> dict[str, ArmPosition]:
    return { name: ArmPosition(reading, arm.position_to_angle(name, reading)) for name, reading in rawpos.items() }

@dataclass
class ServoReading:
    rawpos: int
    angle: float
    speed: int

class Controller:
    settings: Settings

    port: PortHandler | None
    packet_handler: sms_sts | None

    worker_event: threading.Event
    worker_thread: Worker 

    servo_positions: dict[str, ArmPosition] | None = None
    servo_readings: dict[str, ServoReading] | None = None
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

    def joint_set_speed(self, joint_id: int, speed: int, accel: int):
        if not self.packet_handler:
            raise RuntimeError("Undefined packet handler")

        self.packet_handler.WheelMode(joint_id)
        self.packet_handler.WriteSpec(joint_id, speed, accel)

    def disable_torque(self) -> None:
        if not self.packet_handler:
            raise RuntimeError("Undefined packet handler")
        
        for joint in default_settings.servo.joints:
            self.packet_handler.NormalMode(joint.id)

        arm.disable_all_torque(self.packet_handler)

    def get_pos_all(self):
        if not self.packet_handler:
            raise RuntimeError("Undefined packet handler")

        raw = arm.read_all(self.packet_handler)
        self.servo_positions = format_raw_pos(raw)
        return self.servo_positions
    
    def get_pos_speed_all(self):
        if not self.packet_handler:
            raise RuntimeError("Undefined packet handler")
        
        readings: dict[str, ServoReading] = {}

        for joint in default_settings.servo.joints:
            position, speed, result, error = self.packet_handler.ReadPosSpeed(joint.id)

            arm.check_result(self.packet_handler, result, error, f"Read servo {joint.id}")
            
            readings[joint.name] = ServoReading(position, arm.position_to_angle(joint.name, position), speed)

        self.servo_readings = readings

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

from dataclasses import dataclass
from pathlib import Path
import threading
import time

import numpy as np

from modules.scservo_sdk.port_handler import PortHandler
from modules.settings_loader import JointSettings, Settings, default_settings
from modules.scservo_sdk.sms_sts import sms_sts

import modules.arm_helpers as arm 
from logger import logger

from collections import deque

from abc import ABC, abstractmethod

MAX_TICKS = default_settings.servo.configs["ticks_per_revolution"] or 4096
LOG_DIR = Path(__file__).resolve().parent.parent / "modules/logs"
existing_log_numbers = (
    int(path.stem)
    for path in LOG_DIR.glob("*.csv")
    if path.stem.isdecimal()
)
DIAGNOSTIC_LOG_PATH = LOG_DIR / f"{max(existing_log_numbers, default=0) + 1}.csv" # Just number the logs sequentially, not using timestamps
DIAGNOSTIC_FIELDNAMES = ["elapsed_seconds", "delta_seconds"]
# for configured_joint in default_settings.servo.joints:
#     DIAGNOSTIC_FIELDNAMES.extend(
#         (f"{configured_joint.name}_rawpos", f"{configured_joint.name}_angle")
#     )
_diagnostic_log_initialized = False

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

        # Stolen from https://math.stackexchange.com/questions/1649841/signed-angle-difference-without-conditions/1649850#1649850
        delta = (rawpos - curpos + 3/2*MAX_TICKS) % MAX_TICKS - MAX_TICKS/2 
        dist = abs(delta)

        if not self.set_direction:
            self.speed *= sign(delta)
            self.set_direction = True

        # TODO: Current logic can completely overshoot the target position, maybe a dynamic solution involving the speed?
        # For funny result try running at default speed (3000)
        if dist <= self.speed or sign(self.speed) != sign(delta):
            controller.joint_set_speed(self.joint.id, 0, self.accel)
            self.finished = True
            return
        
        controller.joint_set_speed(self.joint.id, round(self.speed), self.accel)

# Naive approach to moving all joints by using normal mode
class MoveJointsNaive(WorkerInstruction):
    def __init__(self, joints: dict[str, int], speed: int = 500, accel: int = 200) -> None:
        super().__init__()

        self.speed = speed
        self.accel = accel

        self.joints = joints
        self.sent_command = False
        self.is_moving = False

    def run(self) -> None:
        super().run()

        if not controller.packet_handler:
            return

        if self.sent_command:
            for jname in self.joints.keys():
                joint_id = next(j.id for j in default_settings.servo.joints if j.name == jname)
                moving, result, error = controller.packet_handler.ReadMoving(joint_id)
                arm.check_result(
                    controller.packet_handler,
                    result,
                    error,
                    f"Read moving status for servo {joint_id}",
                )

                # Some BS yeah but whatevers
                self.is_moving = not not moving

            self.finished = not self.is_moving
            return

        # speed = default_settings.servo.configs["move_speed"]
        speed = self.speed
        accel = self.accel
        try:
            for name, pos in self.joints.items():
                joint_id = next(j.id for j in default_settings.servo.joints if j.name == name)
                res = controller.packet_handler.SyncWritePosEx(joint_id, pos, speed, accel)

                if not res:
                    raise RuntimeError(f"An error was raised when adding {name} to synchronized move")

            result = controller.packet_handler.groupSyncWrite.txPacket()
            if result != arm.COMM_SUCCESS:
                raise RuntimeError(controller.packet_handler.getTxRxResult(result))
        finally:
            controller.packet_handler.groupSyncWrite.clearParam()
            self.sent_command = True

class GripperClose(WorkerInstruction):
    def __init__(self) -> None:
        super().__init__()

        self.sentCommand = False
        self.runningAverageList: deque[int] = deque()
    
    def run(self) -> None:
        speed = 1000
        accel = 100

        if not controller.packet_handler:
            self.finished = True
            raise RuntimeError("Packet handler uninitialized")
        if not controller.servo_readings:
            self.finished = True
            raise RuntimeError("Servo readings uninitialized")

        joint_id = next(j.id for j in default_settings.servo.joints if j.name == "gripper")
        if not self.sentCommand:
            controller.joint_goto_pos(joint_id, 1670, speed, accel)
            self.sentCommand = True

        gripper_reading = controller.servo_readings["gripper"]
        
        # Quit if its too tight ( ͡° ͜ʖ ͡°)
        moving, result, error = controller.packet_handler.ReadMoving(joint_id)
        arm.check_result(
            controller.packet_handler,
            result,
            error,
            f"Read moving status for servo {joint_id}",
        )

        if not moving:
            logger.debug(f"Hey {joint_id}")

        self.finished = not moving

        self.runningAverageList.append(gripper_reading.speed)
        if len(self.runningAverageList) == 5:
            avg = sum(self.runningAverageList) // 5
            if abs(avg) <= 50:
                self.finished = True
                return

            self.runningAverageList.popleft()
        

class GripperOpen(WorkerInstruction):
    def __init__(self) -> None:
        super().__init__()

        self.sentCommand = False 
        self.waitToFinish = True

    def run(self) -> None:
        joint_id = next(j.id for j in default_settings.servo.joints if j.name == "gripper")

        if not controller.packet_handler:
            self.finished = True
            raise RuntimeError("Packet handler uninitialized")

        if not self.sentCommand:
            controller.joint_goto_pos(joint_id, 1275, 1000, 254)
            self.sentCommand = True
            if not self.waitToFinish:
                self.finished = True
                return

        moving, result, error = controller.packet_handler.ReadMoving(joint_id)
        arm.check_result(
            controller.packet_handler,
            result,
            error,
            f"Read moving status for servo {joint_id}",
        )

        self.finished = not moving

class SingleJointSpeedDiag(WorkerInstruction):
    duration_seconds = 3

    def __init__(self, joint: JointSettings, speed: int, accel: int) -> None:
        super().__init__()

        self.joint = joint
        self.speed = speed
        self.accel = accel
        self.started_at: float | None = None
        self.last_tick_at: float | None = None

        self.data = []

        LOG_DIR.mkdir(parents=True, exist_ok=True)
        global _diagnostic_log_initialized
        if not _diagnostic_log_initialized:
            np.savetxt(
                DIAGNOSTIC_LOG_PATH,
                np.empty((0, len(DIAGNOSTIC_FIELDNAMES))),
                delimiter=",",
                header=",".join(DIAGNOSTIC_FIELDNAMES + [self.joint.name]),
                comments="",
            )
            _diagnostic_log_initialized = True

    def run(self):
        super().run()
        if controller.servo_readings is None:
            self.finished = True
            raise RuntimeError("Servo readings required.")

        elapsed = 0.0
        delta = 0.0

        now = time.monotonic()
        if self.started_at is None:
            self.started_at = now
            self.last_tick_at = now
        elif self.last_tick_at is not None:
            elapsed = now - self.started_at
            delta = now - self.last_tick_at
            self.last_tick_at = now

        row = [elapsed, delta]
        reading = controller.servo_readings[self.joint.name]
        row.append(reading.rawpos)

        self.data.append(row)

        if elapsed >= (self.duration_seconds + 1):
            self.finished = True

            with DIAGNOSTIC_LOG_PATH.open("ab") as log_file:
                np.savetxt(log_file, np.asarray(self.data), delimiter=",")
            return

        if elapsed >= self.duration_seconds:
            controller.joint_set_speed(self.joint.id, 0, self.accel)

            return 

        controller.joint_set_speed(self.joint.id, self.speed, self.accel)

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
        while not self.stopped.wait(0):
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
    accel: int
    readtime: float

class Controller:
    settings: Settings

    port: PortHandler | None
    packet_handler: sms_sts | None

    worker_event: threading.Event
    worker_thread: Worker 

    servo_positions: dict[str, ArmPosition] | None = None # Deprecated?

    servo_readings: dict[str, ServoReading] | None = None

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or default_settings
        self.port = None
        self.packet_handler = None

        self.debug = 0

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
    def joint_goto_pos(self, joint_id: int, pos: int, speed: int, accel: int):
        if not self.packet_handler:
            raise RuntimeError("Undefined packet handler")

        self.packet_handler.NormalMode(joint_id)
        result, error = self.packet_handler.write1ByteTxRx(
            joint_id,
            arm.SMS_STS_TORQUE_ENABLE,
            1,
        )
        arm.check_result(
            self.packet_handler,
            result,
            error,
            f"Enable torque for ID {joint_id}",
        )

        result, error = self.packet_handler.WritePosEx(
            joint_id,
            pos,
            speed,
            accel,
        )
        arm.check_result(
            self.packet_handler,
            result,
            error,
            f"Register move for ID {joint_id}",
        )

        logger.info(f"Move sent to ID {joint_id} at position {pos}.")

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
            position, result, error = self.packet_handler.ReadPos(joint.id)
            new_reading_time = time.monotonic()

            arm.check_result(self.packet_handler, result, error, f"Read servo {joint.id}")
            
            speed = 0
            accel = 0

            if self.servo_readings:
                reading = self.servo_readings[joint.name]

                delta_displacement = (position - reading.rawpos + 3/2*MAX_TICKS) % MAX_TICKS - MAX_TICKS/2 

                dt = new_reading_time - reading.readtime
                speed = round(delta_displacement/dt)
                accel = round((speed - reading.speed)/dt)
            
            readings[joint.name] = ServoReading(position, arm.position_to_angle(joint.name, position), speed, accel, new_reading_time)

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

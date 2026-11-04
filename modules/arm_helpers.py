"""Small helpers shared by the standalone task programs."""

from pathlib import Path
import sys
import time

PROJECT_FOLDER = Path(__file__).resolve().parent
if str(PROJECT_FOLDER) not in sys.path:
    sys.path.insert(0, str(PROJECT_FOLDER))

from scservo_sdk import COMM_SUCCESS, SMS_STS_TORQUE_ENABLE, PortHandler, sms_sts

from settings_loader import default_settings

settings = default_settings
joint_names = [j.name for j in settings.servo.joints]
servo_ids = [j.id for j in settings.servo.joints]

def connect():
    """Open the servo serial port and return its SDK packet handler."""
    port = PortHandler(settings.connection.serial_port)
    if not port.openPort():
        raise RuntimeError(f"Could not open serial port {settings.connection.serial_port}")
    if not port.setBaudRate(settings.connection.baud_rate):
        port.closePort()
        raise RuntimeError(f"Could not set baud rate to {settings.connection.baud_rate}")
    return port, sms_sts(port)


def check_result(packet_handler, result, error, action):
    if result != COMM_SUCCESS:
        raise RuntimeError(f"{action}: {packet_handler.getTxRxResult(result)}")
    if error:
        raise RuntimeError(f"{action}: {packet_handler.getRxPacketError(error)}")


def disable_all_torque(packet_handler):
    """Release torque on every configured servo, reporting any failures."""
    failures = []
    for joint in settings.servo.joints:
        name = joint.name
        servo_id = joint.id
        result, error = packet_handler.write1ByteTxRx(
            servo_id, SMS_STS_TORQUE_ENABLE, 0
        )
        try:
            check_result(packet_handler, result, error, f"Disable torque for {name}")
        except RuntimeError as failure:
            failures.append(str(failure))
    if failures:
        raise RuntimeError("Emergency stop incomplete: " + "; ".join(failures))


def enable_all_torque(packet_handler):
    """Enable torque on every configured servo, reporting any failures."""
    failures = []
    for joint in settings.servo.joints:
        name = joint.name
        servo_id = joint.id
        result, error = packet_handler.write1ByteTxRx(
            servo_id, SMS_STS_TORQUE_ENABLE, 1
        )
        try:
            check_result(packet_handler, result, error, f"Enable torque for {name}")
        except RuntimeError as failure:
            failures.append(str(failure))
    if failures:
        raise RuntimeError("Could not enable all servos: " + "; ".join(failures))


def wait_for_servos_or_estop(packet_handler, servo_ids, terminal):
    """Wait until every move finishes, or release torque when Space is pressed."""
    while True:
        key = terminal.read_key(0.02)
        if key == " ":
            print("\nEMERGENCY STOP: releasing torque on all servos.", flush=True)
            disable_all_torque(packet_handler)
            return False

        moving_servos = []
        for servo_id in servo_ids:
            moving, result, error = packet_handler.ReadMoving(servo_id)
            check_result(
                packet_handler,
                result,
                error,
                f"Read moving status for servo {servo_id}",
            )
            if moving:
                moving_servos.append(servo_id)
        if not moving_servos:
            return True
        time.sleep(0.02)


def read_servo(packet_handler, servo_id):
    position, result, error = packet_handler.ReadPos(servo_id)
    check_result(packet_handler, result, error, f"Read servo {servo_id}")
    return position


def read_all(packet_handler):
    return {
        joint.name: read_servo(packet_handler, joint.id)
        for joint in settings.servo.joints
    }


def move_all_sync(packet_handler, positions, speed=None, acceleration=None):
    """Send selected servo targets in one synchronized SDK packet."""
    move_positions_sync(
        packet_handler,
        positions,
        joint_names,
        speed=speed,
        acceleration=acceleration,
    )


def move_positions_sync(
    packet_handler, positions, joint_names, speed=None, acceleration=None
):
    """Send named servo targets in one synchronized SDK packet."""
    if speed is None:
        speed = settings.servo.configs["move_speed"]
    if acceleration is None:
        acceleration = settings.servo.configs["move_acceleration"]
    try:
        for name in joint_names:
            position = int(positions[name])
            if not 0 <= position <= 4095:
                raise ValueError(f"{name} position must be between 0 and 4095")
            added = packet_handler.SyncWritePosEx(
                servo_ids[name],
                position,
                speed,
                acceleration,
            )
            if not added:
                raise RuntimeError(f"Could not add {name} to synchronized move")
        result = packet_handler.groupSyncWrite.txPacket()
        if result != COMM_SUCCESS:
            raise RuntimeError(packet_handler.getTxRxResult(result))
    finally:
        packet_handler.groupSyncWrite.clearParam()


def angle_to_position(name, angle_degrees):
    joint = next((j for j in settings.servo.joints if j.name == name), None)
    if not joint:
        raise ValueError(f"Unknown joint name: {name}")

    minimum, maximum = joint.angle_limits
    if not minimum <= angle_degrees <= maximum:
        raise ValueError(
            f"{name} angle {angle_degrees:.2f} is outside the configured "
            f"limits [{minimum:.2f}, {maximum:.2f}] degrees"
        )
    position = round(
        joint.zero_ticks
        + joint.directions
        * angle_degrees
        * settings.servo.configs["ticks_per_revolution"]
        / 360.0
    )
    if not 0 <= position <= 4095:
        raise ValueError(
            f"{name} angle maps to raw position {position}, outside 0-4095"
        )
    return position


def position_to_angle(name, position):
    joint = next((j for j in settings.servo.joints if j.name == name), None)
    if not joint:
        raise ValueError(f"Unknown joint name: {name}")
    if not 0 <= position <= 4095:
        raise ValueError(f"{name}: raw position must be between 0 and 4095")
    return (
        (position - joint.zero_ticks)
        * 360.0
        / (joint.directions * settings.servo.configs["ticks_per_revolution"]
)
    )


def positions_to_angles(positions):
    return {
        name: position_to_angle(name, positions[name])
        for name in joint_names
    }

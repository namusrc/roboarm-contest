import cmd

from modules import arm_controller
from modules.logger import logger
from modules.settings_loader import default_settings
from modules.arm_controller import controller, MoveSingleJoint, DisableTorque, SingleJointSpeedDiag, MoveJointsNaive
from modules.waypoint_manager import wp_manager
from modules.sequence_manager import SequenceManager, SequenceWaypoint

class Shell():
    def __init__(self) -> None:
        self._sequence_manager: SequenceManager | None = None

    def do_connect(self):
        controller.connect()

    def do_reconnect(self):
        controller.reconnect()

    def do_echo(self, line: str, *args: list[str]):
        logger.info(self.format(line))

    def do_conexec(self, methodname: str, *args):
        try: 
            method = getattr(controller, methodname)

            if callable(method):
                method()
        except AttributeError:
            logger.error(f"No controller method named {methodname}")
    
    def do_torqueoff(self) -> None:
        controller.worker_thread.inst_queue.append(DisableTorque()) 

    def do_movesj(self, joint_id, rawpos, speed = None, accel = None):
        if not joint_id or not rawpos:
            raise ValueError("Expected two arguments: joint_id, rawpos") 
        
        joint_id = int(joint_id)
        rawpos = int(rawpos)
        speed = int(speed) if speed else default_settings.servo.configs["move_speed"]
        accel = int(accel) if accel else default_settings.servo.configs["move_acceleration"]


        joint = next(j for j in default_settings.servo.joints if j.id == joint_id)

        logger.info(f"Moving single joint {joint.name} id {joint.id} to {rawpos}.")
        controller.worker_thread.inst_queue.append(MoveSingleJoint(joint, rawpos, speed, accel))

    def do_sjspeeddiag(self, joint_id, speed = None, accel = None):
        if not joint_id:
            raise ValueError("Expected arguments: joint_id") 

        joint_id = int(joint_id)
        speed = int(speed) if speed else 500
        accel = int(accel) if accel else default_settings.servo.configs["move_acceleration"]

        joint = next(j for j in default_settings.servo.joints if j.id == joint_id)

        controller.worker_thread.inst_queue.append(SingleJointSpeedDiag(joint, speed, accel))

    # def do_sjspeed(self, joint_id, speed = None, accel = None):
    #     if not joint_id:
    #         raise ValueError("Expected arguments: joint_id") 
    #
    #     joint_id = int(joint_id)
    #     speed = int(speed) if speed else 500
    #     accel = int(accel) if accel else default_settings.servo.configs["move_acceleration"]
    #
    #     joint = next(j for j in default_settings.servo.joints if j.id == joint_id)
    #     controller.worker_thread.inst_queue.append(SetSpeedInstructionSingle(joint, speed, accel))
    #

    def do_savewp(self, file = "default") -> None:
        if not controller.servo_readings:
            raise ValueError("Controller servo readings not found")

        readings = controller.servo_readings.values() 
        readings_rawpos = [r.rawpos for r in readings]
        wp_manager.writeWaypoint(readings_rawpos, file)

    def do_gotowp(self, wp_id: str, file = "default") -> None:
        wp_id_num = int(wp_id)
        waypoints = wp_manager.getWaypoints(file)
        waypoint = next((wp for wp in waypoints if wp[0] == wp_id_num), None)
        
        if not waypoint:
            logger.warning(f"Waypoint with ID {wp_id} in file {file} could not be found.")
            return
        waypoint = waypoint[1:]
        servo_names = [j.name for j in default_settings.servo.joints]
        logger.info(f"Waypoint ID {wp_id} at {file}.csv found: {waypoint}")
        controller.worker_thread.inst_queue.append(MoveJointsNaive({ name: waypoint[i] for i, name in enumerate(servo_names)}))
    
    def do_sequence(self, cmd: str, *args: str):
        if cmd == "start":
            if self._sequence_manager is not None:
                logger.warning("Sequence started recording already")
                return
            
            self._sequence_manager = SequenceManager()
            return
        if not self._sequence_manager:
            raise RuntimeError("Sequence not started yet")

        match cmd:
            case "save":
                name = args[0]

                if not name:
                    raise ValueError("Please enter a name for your sequence")

                self._sequence_manager.save(name)
                self._sequence_manager = None
            case "record":
                speed, accel = args
                speed_int = int(speed) if speed else default_settings.servo.configs["move_speed"]
                accel_int = int(accel) if accel else default_settings.servo.configs["move_acceleration"]

                if not controller.servo_readings:
                    raise RuntimeError("Servo readings not initalized")

                readings = controller.servo_readings.items() 
                positions = { n: sr.rawpos for n, sr in readings if n != "gripper"}

                self._sequence_manager.waypoints.append(SequenceWaypoint(positions, speed_int, accel_int))
            case "undo":
                self._sequence_manager.waypoints.pop()
            case "clear":
                self._sequence_manager.waypoints.clear()
            case _:
                logger.info("Sequence commands: start, save, record, undo, clear")

    def default(self, cmd: str):
        logger.warning(f"Unknown command: {cmd}")

    def format(self, output: object) -> str:
        return f"(shell) {output}"

    def run(self, line: str) -> None:
        cmd, *args = line.split(" ")
        try:
            method = getattr(self, f"do_{cmd}")
            method(*args)
        except AttributeError:
            self.default(cmd)
        except Exception as err:
            logger.error(f"An error has occured when running the command: {cmd}\n{err}")

shell = Shell()

import cmd

from modules.logger import logger
from modules.settings_loader import default_settings
from modules.arm_controller import controller, MoveSingleJoint, DisableTorque, SingleJointSpeedDiag

class Shell():
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

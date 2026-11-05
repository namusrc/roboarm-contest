import cmd

from modules.logger import logger
from modules.settings_loader import default_settings
from modules.arm_controller import controller

class Shell():
    def do_connect(self):
        controller.connect()

    def do_echo(self, line: str, *args: list[str]):
        logger.info(self.format(line))

    def do_conexec(self, methodname: str, *args):
        try: 
            method = getattr(controller, methodname)

            if callable(method):
                method()
        except AttributeError:
            logger.error(f"No controller method named {methodname}")

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

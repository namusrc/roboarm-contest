from textual.widgets import Input
from textual.binding import Binding

from modules import logger
from modules.shell import shell 

class CommandInput(Input):
    DEFAULT_CSS = """
    CommandInput {
        margin: 0;
    }
    """

    BINDINGS = [Binding("escape", "blur", "Blur", show=False)]

    def __init__(self) -> None:
        super().__init__(compact=True)
        self.placeholder = "(i) Execute a command ..."

    def action_blur(self) -> None:
        self.blur()

    def on_input_submitted(self):
        logger.logger.info(self.value)
        shell.run(self.value)
        self.clear()
        self.blur()

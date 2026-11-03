from typing import Callable, Deque

from textual.app import CommandCallback, ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, RichLog

import ui_globals

from modules import logger

class LogWidget(RichLog):
    DEFAULT_CSS = """
    LogWidget {
        scrollbar-visibility: hidden;
    }
    """
    def __init__(self) -> None:
        super().__init__(auto_scroll=True, wrap=True)

    def on_log(self, msg: str) -> None:
        self.write(msg)

    def on_mount(self) -> None:
        logger.handler.subscribe(self.on_log)

        logHistory = logger.handler.get_history()
        for log in logHistory:
            self.write(log)

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
        self.clear()
        self.blur()

class Console(Screen):
    BINDINGS = ui_globals.MAIN_FOOTER_BINDINGS + [Binding("i", "input_focus", "Focus", show=False)]

    def on_mount(self) -> None:
        pass

    def action_input_focus(self) -> None:
        self.query_one(CommandInput).focus()

    def compose(self) -> ComposeResult:
        yield Header()
        yield LogWidget()
        yield CommandInput()
        yield Footer()

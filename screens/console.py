from typing import Callable, Deque

from textual.app import CommandCallback, ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Input

import ui_globals

from modules import logger
from modules.shell import shell 

from widgets.LogWidget import LogWidget
from widgets.CommandInput import CommandInput

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

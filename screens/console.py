from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Log

import ui_globals

class Console(Screen):
    BINDINGS = ui_globals.MAIN_FOOTER_BINDINGS
    DEFAULT_CSS = """
    Log {
        scrollbar-visibility: hidden;
    }
    """

    def on_mount(self) -> None:
        self.logInstance.write_line("Test")
        self.logInstance.write_line("Lorem ipsum dolor sit amet, consectetur adipiscing elit. In laoreet ligula velit, a aliquam est volutpat nec. Sed odio mi, faucibus sit amet nunc quis, suscipit ultrices tellus. Praesent ut sollicitudin dui. Praesent at fringilla ipsum. Suspendisse vestibulum, turpis quis semper porttitor, ante diam vestibulum nisl, a ornare sem velit in lacus.")

    def compose(self) -> ComposeResult:
        self.logInstance = Log(auto_scroll=True)
        yield Header()
        yield self.logInstance
        yield Footer()

from modules import logger
from textual.widgets import RichLog

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

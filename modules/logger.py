import logging
from typing import Any, Callable, Deque
from collections import deque

logger = logging.getLogger()
logger.setLevel(0)

LOG_HISTORY_MAX_DEFAULT = 64
class Handler(logging.Handler):
    _callbacks: list[Callable[[str], Any]]
    _history: Deque[logging.LogRecord]
    history_max_length: int 

    def __init__(self) -> None:
        super().__init__()
        
        self._callbacks = []
        self._history = deque()
        self.history_max_length = LOG_HISTORY_MAX_DEFAULT

        loggingFormat = logging.Formatter("[{asctime} {name}]({levelname}) > {message}", style="{")
        self.setFormatter(loggingFormat)
    
    def emit(self, record):
        if len(self._history) > self.history_max_length:
            self._history.pop()
        self._history.append(record)

        for cb in self._callbacks:
            cb(self.format(record))

    def get_history(self) -> list[str]:
        return [self.format(rec) for rec in self._history]

    def subscribe(self, callback: Callable[[str], Any]):
        self._callbacks.append(callback)

    def unsubscribe(self, callback: Callable[[str], Any]):
        try:
            self._callbacks.remove(callback)
        except:
            logger.warning(f"Failed to remove callback {callback}")

handler = Handler()
logger.addHandler(handler)

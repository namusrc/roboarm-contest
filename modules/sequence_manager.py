from collections import deque
from dataclasses import dataclass, asdict
import json
from pathlib import Path
from modules.logger import logger

SEQUENCES_DIR = Path(__file__).resolve().parent.parent / "sequences"
@dataclass
class SequenceWaypoint:
    positions: dict[str, int]
    speed: int
    accel: int

class SequenceManager:
    def __init__(self) -> None:
        SEQUENCES_DIR.mkdir(exist_ok=True)
        self.waypoints: deque[SequenceWaypoint] = deque()
    def getFilePath(self, fileName: str):
        return Path(SEQUENCES_DIR / (fileName + ".json"))
    def getWaypoints(self):
        return [asdict(wp) for wp in self.waypoints]
    def save(self, fileName = "default"):
        filePath = self.getFilePath(fileName)
        if not filePath.is_file():
            logger.info(f"Saved sequence at {filePath}")
            with open(filePath, "w") as f:
                f.write(json.dumps(self.getWaypoints(), indent=4))
        else:
            raise RuntimeError("File already exists!")

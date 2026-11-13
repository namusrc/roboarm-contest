from collections import deque
from dataclasses import dataclass, asdict
import json
from pathlib import Path
from typing import Any
from modules.logger import logger

SEQUENCES_DIR = Path(__file__).resolve().parent.parent / "sequences"
@dataclass
class SequenceWaypoint:
    positions: dict[str, int]
    speed: int
    accel: int

    @classmethod
    def from_dict(cls, i_dict: dict[str, Any]):
        return cls(i_dict["positions"], i_dict["speed"], i_dict["accel"])

class SequenceManager:
    def __init__(self) -> None:
        SEQUENCES_DIR.mkdir(exist_ok=True)
        self.waypoints: deque[SequenceWaypoint] = deque()
    @staticmethod
    def getFilePath(fileName: str):
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
    @staticmethod
    def load(fileName: str) -> list[SequenceWaypoint]:
        filePath = SequenceManager.getFilePath(fileName)
        if not filePath.is_file():
            raise ValueError(f"Sequence file with path {filePath} does not exist!")
        
        with open(filePath) as f:
            fc = f.read()
            if not fc:
                logger.warning("Sequence file empty")
            wp_arr: list[dict[str, object]] = json.loads(fc)
            return [SequenceWaypoint.from_dict(wp) for wp in wp_arr] 

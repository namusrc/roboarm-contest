from collections import deque
from dataclasses import dataclass, asdict
import json
from pathlib import Path
from typing import Any, Literal
from modules.logger import logger

SEQUENCES_DIR = Path(__file__).resolve().parent.parent / "sequences"

@dataclass
class SequenceObject:
    pass

@dataclass
class SequenceWaypoint(SequenceObject):
    positions: dict[str, int]
    speed: int
    accel: int

    @classmethod
    def from_dict(cls, i_dict: dict[str, Any]):
        return cls(i_dict["positions"], i_dict["speed"], i_dict["accel"])

@dataclass
class SequenceGripper(SequenceObject):
    move: str

    @classmethod
    def from_dict(cls, i_dict: dict[str, Any]):
        return cls(i_dict["move"])

class SequenceManager:
    def __init__(self) -> None:
        SEQUENCES_DIR.mkdir(exist_ok=True)
        self.waypoints: deque[SequenceObject] = deque()
    @staticmethod
    def getFilePath(fileName: str):
        return Path(SEQUENCES_DIR / (fileName + ".json"))
    def getWaypoints(self):
        def format(wp: SequenceObject):
            if isinstance(wp, SequenceGripper):
                return { "type": "gripper", "data": asdict(wp) }
            elif isinstance(wp, SequenceWaypoint):
                return { "type": "waypoint", "data": asdict(wp) }

        return [format(wp) for wp in self.waypoints]
    def save(self, fileName = "default"):
        filePath = self.getFilePath(fileName)
        if not filePath.is_file():
            logger.info(f"Saved sequence at {filePath}")
            with open(filePath, "w") as f:
                f.write(json.dumps(self.getWaypoints(), indent=4))
        else:
            raise RuntimeError("File already exists!")
    @staticmethod
    def load(fileName: str) -> list[SequenceObject]:
        filePath = SequenceManager.getFilePath(fileName)
        if not filePath.is_file():
            raise ValueError(f"Sequence file with path {filePath} does not exist!")
        
        with open(filePath) as f:
            fc = f.read()
            if not fc:
                logger.warning("Sequence file empty")
            wp_arr: list[dict[str, Any]] = json.loads(fc)
            return [SequenceWaypoint.from_dict(wp["data"]) if wp["type"] == "waypoint" else SequenceGripper.from_dict(wp["data"]) for wp in wp_arr] 

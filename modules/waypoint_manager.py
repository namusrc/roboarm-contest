from modules.logger import logger
from pathlib import Path
from modules.settings_loader import default_settings

WAYPOINTS_DIR = Path(__file__).resolve().parent.parent / "waypoints"

class WaypointManager:
    def __init__(self):
        WAYPOINTS_DIR.mkdir(exist_ok=True)
    def getFilePath(self, fileName: str):
        return Path(WAYPOINTS_DIR / (fileName + ".csv"))
    def initFile(self, fileName = "default"):
        filePath = self.getFilePath(fileName)
        if not filePath.is_file():
            logger.info(f"Initialized file at {filePath}")
            with open(filePath, "w") as f:
                header = ["id"] +  [j.name for j in default_settings.servo.joints]
                headerStr = ",".join(header)
                f.write(headerStr + "\n")

        return filePath
    def readFile(self, fileName = "default") -> str:
        filePath = self.getFilePath(fileName)
        
        with open(filePath) as f:
            return f.read()
    def getWaypoints(self, fileName = "default") -> list[list[int]]:
        fileContents = self.readFile(fileName)
        lines = fileContents.strip().split("\n")[1:]
        lines_split = [l.split(",") for l in lines]
        return [[int(l) for l in line] for line in lines_split]

    def writeWaypoint(self, readings: list[int], fileName = "default"):
        filePath = self.initFile(fileName)
        existingWaypoints = self.getWaypoints(fileName)
        
        wp_id = str(existingWaypoints[-1][0] + 1) if len(existingWaypoints) else "0"
        
        logger.info(f"Writing to {filePath}")
        with open(filePath, "a") as f:
            f.write(",".join([wp_id] + [str(r) for r in readings]) + "\n")

wp_manager = WaypointManager()

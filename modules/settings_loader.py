from dataclasses import dataclass
import json

@dataclass
class ConnectionSettings:
    serial_port: str
    baud_rate: int

    @classmethod
    def from_json(cls, data: dict):
        return cls(data["serial_port"], data["baud_rate"])

@dataclass
class JointSettings:
    name: str
    id: int
    zero_ticks: int
    directions: int
    angle_limits: tuple[int, int]

@dataclass
class ServoSettings:
    configs: dict[str, int]
    joints: list[JointSettings]

    @classmethod
    def from_json(cls, data: dict):
        joints_raw: dict = data["joints"]
        joints_names = joints_raw.keys()
        joints: list[JointSettings] = []
        for name in joints_names:
            joint: dict = joints_raw[name]
            joints.append(JointSettings(name, joint["id"], joint["zero_ticks"], joint["directions"], tuple(joint["angle_limits"])))
        return cls(data["configs"], joints)

@dataclass
class Settings:
    connection: ConnectionSettings
    servo: ServoSettings

    @classmethod
    def from_json(cls, data: dict):
        return cls(ConnectionSettings.from_json(data["connection"]), ServoSettings.from_json(data["servo"]))

import json
with open("./settings/arm_default.json") as f:
    default_settings = Settings.from_json(json.loads(f.read()))

import math
import numpy as np


def rot(axis, angle):
    axis = np.asarray(axis, dtype=float)
    axis = axis / np.linalg.norm(axis)

    x, y, z = axis

    K = np.array([
        [0, -z, y],
        [z, 0, -x],
        [-y, x, 0]
    ])

    return (
        np.eye(3)
        + math.sin(angle) * K
        + (1 - math.cos(angle)) * (K @ K)
    )


def transform(pos, R=None):
    M = np.eye(4)

    if R is not None:
        M[:3, :3] = R

    M[:3, 3] = pos

    return M


def forward_kinematics(base_deg, shoulder_deg, elbow_deg, wrist_deg):
    b = math.radians(base_deg+90)
    s = math.radians(shoulder_deg+90)
    e = math.radians(elbow_deg-90)
    w = math.radians(wrist_deg+90)
    base_axis = np.array([0, 0, -1])
    pitch_axis = np.array([-0.9402479141,-0.3404906166,0])
    M = np.eye(4)
    M = M @ transform([0, 0, 0.0497])
    M = M @ transform([0, 0, 0], rot(base_axis, b))
    M = M @ transform([-0.001148084157,0.05207040333,0.0577])
    M = M @ transform([0, 0, 0], rot(pitch_axis, s))
    M = M @ transform([-0.006135781789,0.01841212569,0.1189216373])
    M = M @ transform([0, 0, 0], rot(pitch_axis, e))
    M = M @ transform([0.03923147545,-0.1080420757,0.1033874809])
    M = M @ transform([0, 0, 0], rot(pitch_axis, w))
    M = M @ transform([-0.005424859534,-0.03274477062,-0.06924533122])
    M = M @ transform([0.005532242792,-0.06300226309,-0.1462409799])
    x, y, z = M[:3, 3]
    print(M)

    return {
        "tool_tip": (
            float(x),
            float(y),
            float(z)
        )
    }
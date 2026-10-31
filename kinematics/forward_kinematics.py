import math
L2 = 114.0
L3 = 159.0
tool_offset = 47+14
L4 = 106.0 + tool_offset

def forward_kinematics(base,shoulder,elbow,wrist):
    """base,shoulder,elbow,wrist: degrees
    L2: shoulder to elbow length
    L3: elbow to wrist length
    L4: wrist to tool tip length"""
    base2 = math.radians(base)
    shoulder2 = math.radians(shoulder)
    elbow2 = math.radians(elbow)
    wrist2 = math.radians(wrist)
    totalreach = (L2 * math.cos(shoulder2) + L3 * math.cos(shoulder2 + elbow2) + L4 * math.cos(shoulder2 + wrist2 + elbow2))
    z = (L2 * math.sin(shoulder2) + L3 * math.sin(shoulder2 + elbow2) + L4 * math.sin(shoulder2 + wrist2 + elbow2))
    x = totalreach * math.cos(base2)
    y = totalreach * math.sin(base2)
    return {
        "tool_tip" : (x,y,z)
    }
"""
can_messages.py
───────────────
Python mirror of can_messages.h / can_messages.c

Pack / unpack functions use the same byte layout as the C firmware:

  ECU1 (ID 0x100, DLC 4):
    [0-1]  speed_kmh   uint16 big-endian
    [2]    temp_c      uint8
    [3]    indicator   uint8  (0=OFF, 1=LEFT, 2=RIGHT)

  ECU2 (ID 0x200, DLC 5):
    [0-1]  rpm         uint16 big-endian
    [2]    gear        uint8
    [3]    time_min    uint8
    [4]    time_sec    uint8
"""

import struct
from dataclasses import dataclass

# ── CAN IDs (must match C defines) ───────────────────────────────
CAN_ID_ECU1 = 0x100
CAN_ID_ECU2 = 0x200

# ── Indicator states ──────────────────────────────────────────────
INDICATOR_OFF   = 0
INDICATOR_LEFT  = 1
INDICATOR_RIGHT = 2

INDICATOR_STR = {
    INDICATOR_OFF:   "OFF  ",
    INDICATOR_LEFT:  "LEFT ",
    INDICATOR_RIGHT: "RIGHT",
}

# ── Data classes ──────────────────────────────────────────────────
@dataclass
class ECU1Data:
    speed_kmh: int   = 0
    temp_c:    int   = 80
    indicator: int   = INDICATOR_OFF

@dataclass
class ECU2Data:
    rpm:      int = 0
    gear:     int = 1
    time_min: int = 0
    time_sec: int = 0

# ── Pack ──────────────────────────────────────────────────────────
def ecu1_pack(data: ECU1Data) -> bytes:
    """Serialise ECU1Data → 8-byte CAN payload (DLC=4, pad to 8)."""
    return struct.pack(">HBBxxxx",
                       data.speed_kmh,
                       data.temp_c,
                       data.indicator)

def ecu2_pack(data: ECU2Data) -> bytes:
    """Serialise ECU2Data → 8-byte CAN payload (DLC=5, pad to 8)."""
    return struct.pack(">HBBBxxx",
                       data.rpm,
                       data.gear,
                       data.time_min,
                       data.time_sec)

# ── Unpack ────────────────────────────────────────────────────────
def ecu1_unpack(payload: bytes) -> ECU1Data:
    speed, temp, ind = struct.unpack_from(">HBB", payload)
    return ECU1Data(speed_kmh=speed, temp_c=temp, indicator=ind)

def ecu2_unpack(payload: bytes) -> ECU2Data:
    rpm, gear, t_min, t_sec = struct.unpack_from(">HBBB", payload)
    return ECU2Data(rpm=rpm, gear=gear, time_min=t_min, time_sec=t_sec)

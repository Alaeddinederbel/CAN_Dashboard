"""
test_can_messages.py  —  Unit tests for CAN message pack / unpack
─────────────────────────────────────────────────────────────────
Verifies that the Python pack/unpack functions produce the exact
same byte layout as the C firmware (can_messages.c).

Run with:
    python -m pytest test_can_messages.py -v
    # or without pytest:
    python test_can_messages.py
"""

import struct
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from can_messages import (
    ECU1Data, ECU2Data,
    ecu1_pack, ecu1_unpack,
    ecu2_pack, ecu2_unpack,
    INDICATOR_LEFT, INDICATOR_RIGHT, INDICATOR_OFF,
)

# ── ECU1 tests ────────────────────────────────────────────────────
def test_ecu1_pack_byte_layout():
    """speed=0x0148 (328), temp=89, ind=LEFT → bytes must match C layout."""
    d = ECU1Data(speed_kmh=0x0148, temp_c=89, indicator=INDICATOR_LEFT)
    buf = ecu1_pack(d)
    assert buf[0] == 0x01, f"speed MSB expected 0x01, got 0x{buf[0]:02X}"
    assert buf[1] == 0x48, f"speed LSB expected 0x48, got 0x{buf[1]:02X}"
    assert buf[2] == 89,   f"temp expected 89, got {buf[2]}"
    assert buf[3] == 1,    f"indicator expected 1 (LEFT), got {buf[3]}"

def test_ecu1_roundtrip():
    """pack then unpack must recover original values exactly."""
    original = ECU1Data(speed_kmh=120, temp_c=91, indicator=INDICATOR_RIGHT)
    recovered = ecu1_unpack(ecu1_pack(original))
    assert recovered.speed_kmh == original.speed_kmh
    assert recovered.temp_c    == original.temp_c
    assert recovered.indicator == original.indicator

def test_ecu1_zero():
    """All-zero struct must produce all-zero buffer."""
    d = ECU1Data(speed_kmh=0, temp_c=0, indicator=INDICATOR_OFF)
    buf = ecu1_pack(d)
    assert buf[:4] == bytes(4)

def test_ecu1_max_speed():
    """Max uint16 speed (65535) must survive round-trip."""
    d = ECU1Data(speed_kmh=65535, temp_c=255, indicator=INDICATOR_OFF)
    r = ecu1_unpack(ecu1_pack(d))
    assert r.speed_kmh == 65535
    assert r.temp_c    == 255

# ── ECU2 tests ────────────────────────────────────────────────────
def test_ecu2_pack_byte_layout():
    """rpm=2400 (0x0960), gear=3, min=12, sec=34 → verify each byte."""
    d = ECU2Data(rpm=0x0960, gear=3, time_min=12, time_sec=34)
    buf = ecu2_pack(d)
    assert buf[0] == 0x09, f"rpm MSB expected 0x09, got 0x{buf[0]:02X}"
    assert buf[1] == 0x60, f"rpm LSB expected 0x60, got 0x{buf[1]:02X}"
    assert buf[2] == 3,    f"gear expected 3, got {buf[2]}"
    assert buf[3] == 12,   f"time_min expected 12, got {buf[3]}"
    assert buf[4] == 34,   f"time_sec expected 34, got {buf[4]}"

def test_ecu2_roundtrip():
    original = ECU2Data(rpm=3500, gear=4, time_min=5, time_sec=59)
    recovered = ecu2_unpack(ecu2_pack(original))
    assert recovered.rpm      == original.rpm
    assert recovered.gear     == original.gear
    assert recovered.time_min == original.time_min
    assert recovered.time_sec == original.time_sec

def test_ecu2_idle():
    """Idle state: 850 RPM, gear 1, time 00:00."""
    d = ECU2Data(rpm=850, gear=1, time_min=0, time_sec=0)
    r = ecu2_unpack(ecu2_pack(d))
    assert r.rpm  == 850
    assert r.gear == 1
    assert r.time_min == 0
    assert r.time_sec == 0

def test_ecu2_max_time():
    """time_min=59, time_sec=59 must survive round-trip."""
    d = ECU2Data(rpm=1000, gear=2, time_min=59, time_sec=59)
    r = ecu2_unpack(ecu2_pack(d))
    assert r.time_min == 59
    assert r.time_sec == 59

# ── Runner (no pytest needed) ─────────────────────────────────────
if __name__ == "__main__":
    tests = [
        test_ecu1_pack_byte_layout,
        test_ecu1_roundtrip,
        test_ecu1_zero,
        test_ecu1_max_speed,
        test_ecu2_pack_byte_layout,
        test_ecu2_roundtrip,
        test_ecu2_idle,
        test_ecu2_max_time,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1

    print(f"\n{passed}/{passed+failed} tests passed")
    sys.exit(0 if failed == 0 else 1)

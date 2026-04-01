"""
ecu2_sim.py  —  ECU2 Engine & Time Transmitter
───────────────────────────────────────────────
Simulates ECU2 on the CAN bus.

Transmits ID 0x200 every 100 ms with:
  - RPM derived from speed (realistic gear/RPM relationship)
  - Gear automatically selected from speed
  - Elapsed time counter (minutes : seconds)

Usage:
    python ecu2_sim.py
    python ecu2_sim.py --interface socketcan --channel vcan0

Requirements:
    pip install python-can
"""

import can
import time
import math
import argparse
from can_messages import CAN_ID_ECU2, ECU2Data, ecu2_pack

# ── CLI args ──────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="ECU2 Engine & Time Simulator")
parser.add_argument("--interface", default="virtual", help="python-can interface")
parser.add_argument("--channel",   default="vcan0",   help="CAN channel")
parser.add_argument("--bitrate",   default=500000, type=int)
args = parser.parse_args()

TX_PERIOD  = 0.100   # 100 ms
CYCLE_SECS = 30.0

# ── Engine model ──────────────────────────────────────────────────
# Gear thresholds (km/h) and final drive ratios (simplified)
GEAR_TABLE = [
    (0,  30,  1, 3.50),   # gear 1: 0-30  km/h
    (30, 50,  2, 2.10),   # gear 2: 30-50 km/h
    (50, 70,  3, 1.40),   # gear 3: 50-70 km/h
    (70, 90,  4, 1.00),   # gear 4: 70-90 km/h
    (90, 999, 5, 0.80),   # gear 5: 90+   km/h
]

def speed_profile(t: float) -> float:
    """Same profile as ECU1 — must stay in sync."""
    phase = (t % CYCLE_SECS) / CYCLE_SECS
    return max(0.0, 60.0 * (1.0 - math.cos(2.0 * math.pi * phase)))

def gear_and_rpm(speed_kmh: float) -> tuple[int, int]:
    """
    Select gear from speed table, then compute RPM:
      RPM = (speed_kmh / 3.6) / wheel_radius * gear_ratio * diff_ratio
    Simplified: RPM = speed_kmh * ratio * k
    """
    for lo, hi, gear, ratio in GEAR_TABLE:
        if lo <= speed_kmh < hi:
            rpm_raw = speed_kmh * ratio * 35.0   # 35 = tuning constant
            rpm = max(850, min(7000, int(rpm_raw)))  # idle floor + redline
            return gear, rpm
    return 5, 850  # stopped → idle

# ── Main ──────────────────────────────────────────────────────────
def main():
    print(f"[ECU2] Starting on {args.interface}/{args.channel} @ {args.bitrate} bps")
    print(f"[ECU2] Transmitting ID=0x{CAN_ID_ECU2:03X} every {int(TX_PERIOD*1000)} ms")
    print("[ECU2] Press Ctrl-C to stop\n")

    bus = can.Bus(interface=args.interface,
                  channel=args.channel,
                  bitrate=args.bitrate)

    start    = time.monotonic()
    tx_count = 0

    try:
        while True:
            t = time.monotonic() - start

            speed        = speed_profile(t)
            gear, rpm    = gear_and_rpm(speed)

            # Elapsed time counter
            elapsed      = int(t)
            time_min     = (elapsed // 60) % 60
            time_sec     = elapsed % 60

            data = ECU2Data(
                rpm      = rpm,
                gear     = gear,
                time_min = time_min,
                time_sec = time_sec,
            )

            payload = ecu2_pack(data)
            msg = can.Message(
                arbitration_id=CAN_ID_ECU2,
                data=payload,
                is_extended_id=False
            )
            bus.send(msg)
            tx_count += 1

            if tx_count % 20 == 0:
                print(f"[ECU2] t={t:6.1f}s | "
                      f"RPM={rpm:4d} | "
                      f"Gear={gear} | "
                      f"Time={time_min:02d}:{time_sec:02d} | "
                      f"TX#{tx_count}")

            time.sleep(TX_PERIOD)

    except KeyboardInterrupt:
        print(f"\n[ECU2] Stopped. Total frames sent: {tx_count}")
    finally:
        bus.shutdown()

if __name__ == "__main__":
    main()

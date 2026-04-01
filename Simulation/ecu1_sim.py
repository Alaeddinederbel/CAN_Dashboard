"""
ecu1_sim.py  —  ECU1 Vehicle Status Transmitter
────────────────────────────────────────────────
Simulates ECU1 on the CAN bus.

Transmits ID 0x100 every 100 ms with:
  - Speed following a smooth drive cycle (0 → 120 km/h → 0)
  - Engine temperature that warms up from 20 °C to 90 °C
  - Indicator that blinks LEFT or RIGHT periodically

Usage:
    python ecu1_sim.py                  # uses virtual bus (no hardware)
    python ecu1_sim.py --interface socketcan --channel vcan0
    python ecu1_sim.py --interface pcan    --channel PCAN_USBBUS1

Requirements:
    pip install python-can
"""

import can
import time
import math
import argparse
from can_messages import CAN_ID_ECU1, ECU1Data, ecu1_pack
from can_messages import INDICATOR_OFF, INDICATOR_LEFT, INDICATOR_RIGHT

# ── CLI args ──────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="ECU1 Vehicle Status Simulator")
parser.add_argument("--interface", default="virtual",  help="python-can interface")
parser.add_argument("--channel",   default="vcan0",    help="CAN channel")
parser.add_argument("--bitrate",   default=500000, type=int)
args = parser.parse_args()

TX_PERIOD   = 0.100   # seconds  (100 ms → matches C firmware)
CYCLE_SECS  = 30.0    # one full speed profile loop in 30 s

def speed_profile(t: float) -> int:
    """
    Smooth drive cycle using a sine wave:
      0 s  → 0 km/h
      7.5 s → 120 km/h (peak)
      15 s  → 0 km/h  (slow down)
      22.5 s → 60 km/h (city speed)
      30 s  → 0 km/h  (stop, loop)
    """
    phase = (t % CYCLE_SECS) / CYCLE_SECS  # 0.0 → 1.0
    raw = 60.0 * (1.0 - math.cos(2.0 * math.pi * phase))  # 0→120
    return max(0, min(255, int(raw)))

def temp_profile(t: float) -> int:
    """Engine warms from 20 °C to 90 °C over first 60 s, then holds."""
    warm_secs = 60.0
    ratio = min(t / warm_secs, 1.0)
    return int(20.0 + 70.0 * ratio)

def indicator_state(t: float) -> int:
    """Blink LEFT for 3 s every 20 s, RIGHT for 3 s every 40 s."""
    cycle = t % 40.0
    if 10.0 <= cycle < 13.0:
        return INDICATOR_LEFT
    if 30.0 <= cycle < 33.0:
        return INDICATOR_RIGHT
    return INDICATOR_OFF

# ── Main ──────────────────────────────────────────────────────────
def main():
    print(f"[ECU1] Starting on {args.interface}/{args.channel} @ {args.bitrate} bps")
    print(f"[ECU1] Transmitting ID=0x{CAN_ID_ECU1:03X} every {int(TX_PERIOD*1000)} ms")
    print("[ECU1] Press Ctrl-C to stop\n")

    bus = can.Bus(interface=args.interface,
                  channel=args.channel,
                  bitrate=args.bitrate)

    start = time.monotonic()
    tx_count = 0

    try:
        while True:
            t = time.monotonic() - start

            data = ECU1Data(
                speed_kmh = speed_profile(t),
                temp_c    = temp_profile(t),
                indicator = indicator_state(t),
            )

            payload = ecu1_pack(data)
            msg = can.Message(
                arbitration_id=CAN_ID_ECU1,
                data=payload,
                is_extended_id=False
            )
            bus.send(msg)
            tx_count += 1

            if tx_count % 20 == 0:   # print every 2 s
                ind_str = ["OFF  ", "LEFT ", "RIGHT"][data.indicator]
                print(f"[ECU1] t={t:6.1f}s | "
                      f"Speed={data.speed_kmh:3d} km/h | "
                      f"Temp={data.temp_c:3d} C | "
                      f"Ind={ind_str} | "
                      f"TX#{tx_count}")

            time.sleep(TX_PERIOD)

    except KeyboardInterrupt:
        print(f"\n[ECU1] Stopped. Total frames sent: {tx_count}")
    finally:
        bus.shutdown()

if __name__ == "__main__":
    main()

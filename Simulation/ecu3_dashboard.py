"""
ecu3_dashboard.py  —  ECU3 Dashboard Receiver
──────────────────────────────────────────────
Simulates ECU3: receives CAN frames from ECU1 and ECU2,
decodes them, and renders a live terminal dashboard.

Mirrors the C firmware:
  - Filters on 0x100 (ECU1) and 0x200 (ECU2) only
  - Updates state on every received frame
  - Refreshes the display every 500 ms

Usage:
    python ecu3_dashboard.py
    python ecu3_dashboard.py --interface socketcan --channel vcan0
    python ecu3_dashboard.py --log session.asc   # also save to ASC log

Run in a separate terminal alongside ecu1_sim.py + ecu2_sim.py.

Requirements:
    pip install python-can
"""

import can
import time
import argparse
import threading
import sys
import os
from dataclasses import dataclass, field
from can_messages import (
    CAN_ID_ECU1, CAN_ID_ECU2,
    ECU1Data, ECU2Data,
    ecu1_unpack, ecu2_unpack,
    INDICATOR_STR,
)

# ── CLI args ──────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="ECU3 Dashboard Receiver")
parser.add_argument("--interface", default="virtual", help="python-can interface")
parser.add_argument("--channel",   default="vcan0",   help="CAN channel")
parser.add_argument("--bitrate",   default=500000, type=int)
parser.add_argument("--log",       default=None,
                    help="Optional path to save ASC log (e.g. session.asc)")
args = parser.parse_args()

PRINT_PERIOD = 0.500   # refresh display every 500 ms

# ── Dashboard state ───────────────────────────────────────────────
@dataclass
class DashboardState:
    speed_kmh:  int = 0
    rpm:        int = 0
    gear:       int = 1
    temp_c:     int = 20
    indicator:  int = 0
    time_min:   int = 0
    time_sec:   int = 0
    ecu1_valid: bool = False
    ecu2_valid: bool = False
    ecu1_rx:    int  = 0    # frame counters
    ecu2_rx:    int  = 0
    last_update: float = field(default_factory=time.monotonic)

state = DashboardState()
state_lock = threading.Lock()

# ── ANSI helpers ──────────────────────────────────────────────────
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def color(text: str, code: str) -> str:
    """Wrap text in ANSI color if stdout is a TTY."""
    if sys.stdout.isatty():
        return f"\033[{code}m{text}\033[0m"
    return text

GREEN  = "32"
YELLOW = "33"
CYAN   = "36"
RED    = "31"
BOLD   = "1"
DIM    = "2"

# ── Dashboard renderer ────────────────────────────────────────────
def render(s: DashboardState, elapsed: float):
    """Print a full dashboard frame to the terminal."""
    ind_str   = INDICATOR_STR.get(s.indicator, "OFF  ")
    ind_color = YELLOW if s.indicator else DIM

    # RPM bar (0–7000)
    bar_len  = 30
    rpm_fill = int((s.rpm / 7000.0) * bar_len)
    rpm_bar  = color("█" * rpm_fill, GREEN) + color("░" * (bar_len - rpm_fill), DIM)

    # Speed bar (0–200)
    spd_fill = int((s.speed_kmh / 200.0) * bar_len)
    spd_bar  = color("█" * spd_fill, CYAN) + color("░" * (bar_len - spd_fill), DIM)

    ecu1_status = color("OK", GREEN)  if s.ecu1_valid else color("--", RED)
    ecu2_status = color("OK", GREEN)  if s.ecu2_valid else color("--", RED)

    lines = [
        "",
        color("  ╔══════════════════════════════════════════╗", BOLD),
        color("  ║   CAN DASHBOARD  |  STM32F429  Python    ║", BOLD),
        color("  ╠══════════════════════════════════════════╣", BOLD),
        f"  ║  Time   {color(f'{s.time_min:02d}:{s.time_sec:02d}', CYAN)}          "
        f"Elapsed  {color(f'{elapsed:.0f}s', DIM)}        ║",
        f"  ║  Speed  {color(f'{s.speed_kmh:3d} km/h', CYAN)}  {spd_bar}  ║",
        f"  ║  RPM    {color(f'{s.rpm:4d}    ', CYAN)}  {rpm_bar}  ║",
        f"  ║  Gear   {color(str(s.gear), YELLOW)}              "
        f"Temp    {color(f'{s.temp_c:3d} C', YELLOW)}          ║",
        f"  ║  Ind    {color(ind_str, ind_color)}                                   ║",
        color("  ╠══════════════════════════════════════════╣", BOLD),
        f"  ║  ECU1 {ecu1_status}  RX#{s.ecu1_rx:<6d}   "
        f"ECU2 {ecu2_status}  RX#{s.ecu2_rx:<6d}  ║",
        color("  ╚══════════════════════════════════════════╝", BOLD),
        "",
        color("  Press Ctrl-C to exit", DIM),
    ]
    clear_screen()
    print("\n".join(lines))

# ── CAN receive thread ────────────────────────────────────────────
def rx_thread(bus: can.BusABC, stop_event: threading.Event):
    """
    Runs in a background thread.
    Reads frames from the bus and updates shared state.
    Only processes 0x100 and 0x200 — all others are silently dropped
    (mirrors the hardware filter in ECU3_CAN_FilterConfig).
    """
    while not stop_event.is_set():
        msg = bus.recv(timeout=0.2)
        if msg is None:
            continue

        with state_lock:
            if msg.arbitration_id == CAN_ID_ECU1:
                d = ecu1_unpack(msg.data)
                state.speed_kmh  = d.speed_kmh
                state.temp_c     = d.temp_c
                state.indicator  = d.indicator
                state.ecu1_valid = True
                state.ecu1_rx   += 1
                state.last_update = time.monotonic()

            elif msg.arbitration_id == CAN_ID_ECU2:
                d = ecu2_unpack(msg.data)
                state.rpm        = d.rpm
                state.gear       = d.gear
                state.time_min   = d.time_min
                state.time_sec   = d.time_sec
                state.ecu2_valid = True
                state.ecu2_rx   += 1
                state.last_update = time.monotonic()

# ── Main ──────────────────────────────────────────────────────────
def main():
    print(f"[ECU3] Starting dashboard receiver on {args.interface}/{args.channel}")
    if args.log:
        print(f"[ECU3] Logging to {args.log}")

    listeners = []
    if args.log:
        listeners.append(can.ASCWriter(args.log))

    bus = can.Bus(interface=args.interface,
                  channel=args.channel,
                  bitrate=args.bitrate)

    stop_event = threading.Event()
    rx = threading.Thread(target=rx_thread, args=(bus, stop_event), daemon=True)
    rx.start()

    start   = time.monotonic()
    last_print = 0.0

    print("[ECU3] Waiting for CAN frames...\n")
    time.sleep(0.5)   # let rx thread settle

    try:
        while True:
            now = time.monotonic()
            if (now - last_print) >= PRINT_PERIOD:
                last_print = now
                with state_lock:
                    snap = DashboardState(**state.__dict__)
                render(snap, now - start)

            time.sleep(0.05)

    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        rx.join(timeout=1.0)
        bus.shutdown()
        print("\n[ECU3] Dashboard stopped.")
        print(f"[ECU3] Total frames received — ECU1: {state.ecu1_rx}  ECU2: {state.ecu2_rx}")

if __name__ == "__main__":
    main()

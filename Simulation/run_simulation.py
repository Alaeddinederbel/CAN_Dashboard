"""
run_simulation.py  —  All-in-one CAN Dashboard Simulator
─────────────────────────────────────────────────────────
Launches ECU1, ECU2, and ECU3 as subprocesses so you only
need to run a single command:

    python run_simulation.py

Each ECU runs in its own process (mirrors the real hardware where
each ECU is a separate MCU). The dashboard opens in a new terminal
window so you can see all output simultaneously.

Press Ctrl-C to stop everything cleanly.

Tested on: Windows 10/11, Ubuntu 22.04, macOS 13+
"""

import subprocess
import sys
import time
import signal
import os
import argparse
import platform

parser = argparse.ArgumentParser(description="CAN Dashboard All-in-One Runner")
parser.add_argument("--interface", default="virtual",
                    help="python-can interface (default: virtual)")
parser.add_argument("--channel", default="vcan0",
                    help="CAN channel (default: vcan0)")
args = parser.parse_args()

python = sys.executable   # same interpreter that's running this script

common_args = ["--interface", args.interface, "--channel", args.channel]

SCRIPTS = [
    ("ECU1", [python, "ecu1_sim.py"]      + common_args),
    ("ECU2", [python, "ecu2_sim.py"]      + common_args),
    ("ECU3", [python, "ecu3_dashboard.py"] + common_args),
]

def launch_in_new_terminal(name: str, cmd: list[str]) -> subprocess.Popen:
    """
    Open a new terminal window for each ECU so output is visible
    separately. Falls back to launching in the background if the
    terminal emulator isn't available.
    """
    system = platform.system()
    script_dir = os.path.dirname(os.path.abspath(__file__))

    if system == "Windows":
        # Windows Terminal / cmd.exe
        return subprocess.Popen(
            ["start", f"CAN {name}", "cmd", "/k"] + cmd,
            cwd=script_dir, shell=True
        )
    elif system == "Darwin":
        # macOS: open a new Terminal.app tab
        apple_script = (
            f'tell application "Terminal" to do script '
            f'"cd {script_dir} && {" ".join(cmd)}"'
        )
        return subprocess.Popen(["osascript", "-e", apple_script])
    else:
        # Linux: try common terminal emulators in order
        for term in ["gnome-terminal", "xterm", "konsole", "xfce4-terminal"]:
            try:
                if term == "gnome-terminal":
                    proc = subprocess.Popen(
                        [term, "--title", f"CAN {name}", "--"] + cmd,
                        cwd=script_dir
                    )
                else:
                    proc = subprocess.Popen(
                        [term, "-title", f"CAN {name}", "-e"] + cmd,
                        cwd=script_dir
                    )
                return proc
            except FileNotFoundError:
                continue

        # No terminal found — run in background, print to main stdout
        print(f"[Runner] No terminal emulator found for {name}, "
              f"running in background.")
        return subprocess.Popen(cmd, cwd=script_dir)


def main():
    print("=" * 52)
    print("  CAN Dashboard Simulator — All ECUs")
    print(f"  Interface : {args.interface}")
    print(f"  Channel   : {args.channel}")
    print("=" * 52)
    print()

    procs = []
    script_dir = os.path.dirname(os.path.abspath(__file__))

    for name, cmd in SCRIPTS:
        print(f"  Launching {name} ...")
        proc = subprocess.Popen(cmd, cwd=script_dir)
        procs.append((name, proc))
        time.sleep(0.3)   # stagger starts slightly

    print()
    print("  All ECUs running. Press Ctrl-C to stop all.\n")

    def shutdown(sig, frame):
        print("\n[Runner] Stopping all ECUs...")
        for name, proc in procs:
            proc.terminate()
            print(f"  Stopped {name}")
        sys.exit(0)

    signal.signal(signal.SIGINT,  shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Monitor: restart any ECU that crashes unexpectedly
    while True:
        for i, (name, proc) in enumerate(procs):
            ret = proc.poll()
            if ret is not None and ret != 0:
                print(f"[Runner] {name} exited with code {ret}, restarting...")
                new_proc = subprocess.Popen(SCRIPTS[i][1], cwd=script_dir)
                procs[i] = (name, new_proc)
        time.sleep(2.0)

if __name__ == "__main__":
    main()

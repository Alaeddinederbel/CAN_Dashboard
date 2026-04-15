# CAN Dashboard - STM32F429 Multi-ECU System

A CAN bus dashboard system implemented on an STM32F429ZIT6 microcontroller.  
Three simulated ECUs communicate over a shared CAN bus; a dashboard receiver decodes and displays real-time vehicle data over UART.

The full protocol logic is validated via a **Python software simulation** that runs on any PC without hardware, byte-for-byte compatible with the C firmware.

---

## System Architecture

```
  ┌─────────────────┐     ┌─────────────────┐
  │   ECU 1         │     │   ECU 2         │
  │  Vehicle Status │     │  Engine & Time  │
  │                 │     │                 │
  │  Speed  km/h    │     │  RPM            │
  │  Temp   °C      │     │  Gear           │
  │  Indicator      │     │  Time mm:ss     │
  │                 │     │                 │
  │  TX: ID 0x100   │     │  TX: ID 0x200   │
  └────────┬────────┘     └────────┬────────┘
           │                       │
           └───────────┬───────────┘
                       │
             ══════════╪══════════
                  CAN BUS  500 kbps
             ══════════╪══════════
                       │
           ┌───────────┴──────────────┐
           │   ECU 3 — Dashboard RX   │
           │                          │
           │  CAN filters: 0x100      │
           │               0x200      │
           │  ISR: RX FIFO0           │
           │  Output: UART 115200     │
           └──────────────────────────┘
```

---

## Repository Structure

```
CAN_Dashboard/
├── STM32_Firmware/
│   └── Core/
│       ├── Inc/
│       │   ├── can_messages.h      # Frame structs, IDs, pack/unpack API
│       │   ├── dashboard.h         # Aggregated state + display API
│       │   ├── ecu1.h
│       │   ├── ecu2.h
│       │   ├── ecu3_dashboard.h
│       │   └── main.h
│       └── Src/
│           ├── can_messages.c      # Pure C pack/unpack (no HAL dependency)
│           ├── ecu1.c              # Vehicle status transmitter
│           ├── ecu2.c              # Engine data transmitter
│           ├── ecu3_dashboard.c    # Filter config + RX ISR + task
│           ├── dashboard.c         # State machine + UART formatter
│           ├── main.c              # Entry point (SIM_MODE supported)
│           └── stm32f4xx_it.c      # CAN1_RX0 + SysTick ISRs
├── Simulation/
│   ├── can_messages.py             # Python mirror of C structs (same byte layout)
│   ├── ecu1_sim.py                 # ECU1 transmitter — drive cycle profile
│   ├── ecu2_sim.py                 # ECU2 transmitter — RPM/gear model
│   ├── ecu3_dashboard.py           # Receiver + live terminal dashboard
│   ├── run_simulation.py           # One-command launcher for all 3 ECUs
│   ├── test_can_messages.py        # Unit tests (8/8 pass)
│   └── requirements.txt
└── README.md
```

---

## CAN Frame Layout

### ECU1 : Vehicle Status `ID: 0x100  DLC: 4`

| Byte | Field       | Type   | Unit  | Notes              |
|------|-------------|--------|-------|--------------------|
| 0    | speed MSB   | uint16 | km/h  | big-endian         |
| 1    | speed LSB   | uint16 | km/h  |                    |
| 2    | temperature | uint8  | °C    | 0–255              |
| 3    | indicator   | uint8  | enum  | 0=OFF 1=LEFT 2=RIGHT |

### ECU2 : Engine & Time `ID: 0x200  DLC: 5`

| Byte | Field     | Type   | Unit | Notes      |
|------|-----------|--------|------|------------|
| 0    | RPM MSB   | uint16 | rpm  | big-endian |
| 1    | RPM LSB   | uint16 | rpm  |            |
| 2    | gear      | uint8  | —    | 1–6        |
| 3    | time_min  | uint8  | min  | 0–59       |
| 4    | time_sec  | uint8  | sec  | 0–59       |

---

## Hardware Target

| Component | Detail |
|-----------|--------|
| MCU | STM32F429ZIT6 |
| Core | ARM Cortex-M4 + FPU |
| Clock | 180 MHz |
| CAN | CAN1, 500 kbps, Normal mode |
| UART | USART1, 115200-8N1 |
| CAN pins | PD0 (RX), PD1 (TX) — AF9 |
| UART pins | PA9 (TX), PA10 (RX) — AF7 |
| IDE | STM32CubeIDE + HAL |

---

## Getting Started

### Option A : Software simulation (no hardware required)

```bash
# 1. Install dependency
pip install python-can

# 2. Run all ECUs with one command
cd Simulation
python run_simulation.py
```

Or run each ECU in a separate terminal:

```bash
# Terminal 1 — ECU1
python ecu1_sim.py

# Terminal 2 — ECU2
python ecu2_sim.py

# Terminal 3 — ECU3 live dashboard
python ecu3_dashboard.py
```

Dashboard output:

```
  ╔══════════════════════════════════════════╗
  ║   CAN DASHBOARD  |  STM32F429  Python    ║
  ╠══════════════════════════════════════════╣
  ║  Time   00:14          Elapsed  14s      ║
  ║  Speed   72 km/h  ████████████░░░░░░░░  ║
  ║  RPM    2520      ██████████░░░░░░░░░░  ║
  ║  Gear   3              Temp     089 C    ║
  ║  Ind    LEFT                             ║
  ╠══════════════════════════════════════════╣
  ║  ECU1 OK  RX#140       ECU2 OK  RX#140  ║
  ╚══════════════════════════════════════════╝
```

### Option B : STM32 hardware

1. Open STM32CubeIDE and create a new project targeting **STM32F429ZIT6**
2. Configure peripherals in the `.ioc` file:
   - CAN1: Normal mode, 500 kbps
   - USART1: 115200 baud, TX+RX
   - System clock: 180 MHz via HSE PLL
3. Copy all files from `STM32_Firmware/Core/` into your project's `Core/` folder
4. Add `-DSIM_MODE` to compiler preprocessor defines for synthetic sensor data
5. Build and flash — open a serial terminal at 115200 baud to see the dashboard

---

## Running the Unit Tests

The unit tests verify that the Python simulation produces the **exact same byte layout** as the C firmware:

```bash
cd Simulation
python test_can_messages.py
```

```
  PASS  test_ecu1_pack_byte_layout
  PASS  test_ecu1_roundtrip
  PASS  test_ecu1_zero
  PASS  test_ecu1_max_speed
  PASS  test_ecu2_pack_byte_layout
  PASS  test_ecu2_roundtrip
  PASS  test_ecu2_idle
  PASS  test_ecu2_max_time

8/8 tests passed
```

---

## Key Implementation Details

**CAN Hardware Filters**  
ECU3 configures two 32-bit mask-mode filter banks so the hardware silently drops all frames except `0x100` and `0x200`. This reduces ISR overhead to zero for unrelated traffic on the bus.

**Interrupt-driven receive**  
`CAN1_RX0_IRQHandler` → `HAL_CAN_IRQHandler` → `HAL_CAN_RxFifo0MsgPendingCallback`.  
The callback only unpacks the frame and writes to the dashboard state struct — no UART calls, no blocking operations inside the ISR.

**Non-blocking task design**  
All three ECU tasks use `HAL_GetTick()` for periodic timing. No `HAL_Delay()` anywhere — the main loop runs free and every task self-gates on elapsed time.

**Hardware/Software separation**  
`can_messages.c` has zero HAL includes — it is pure portable C. The Python `can_messages.py` implements the identical byte layout. This means the framing logic can be unit-tested on any machine without an STM32.

---

**Ala Eddine Derbel** - *Embedded Systems Engineer*

# VRCM Robot Control System

A Python-based control system for communicating with robotic vehicles via Connex 4490 radio modules. This system provides remote control capabilities, diagnostics monitoring, path/scenario uploading, and comprehensive robot management.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Hardware Requirements](#hardware-requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Core Components](#core-components)
- [Usage Examples](#usage-examples)
- [Protocol Documentation](#protocol-documentation)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)

---

## Overview

This system enables wireless communication and control of robotic vehicles equipped with Connex 4490 radio modules. It supports:

- Real-time remote control (RC mode)
- Robot discovery and network management
- Power control (on/off)
- Diagnostic data retrieval
- Path/scenario upload for autonomous operation
- Multi-robot coordination across RF channels

The codebase consists of two main files:
- **`test.py`**: Core radio communication, robot control, and RC operations
- **`tester.py`**: Path/scenario management and upload functionality

---

## Features

### Robot Control
- **Remote Control**: Joystick-based movement (X, Y, Z axes)
- **Tower/Torso Control**: Adjustable positioning (up, down, half)
- **Power Management**: Turn robots on/off remotely
- **Multi-Robot Support**: Control up to 8 robots across 3 RF channels

### Communication
- **RF Channel Management**: Switch between channels A (16), B (26), C (37)
- **Network Configuration**: Change robot client IDs and RF assignments
- **Auto-Discovery**: Scan for available robots on all channels
- **Ping/Status Checks**: Verify robot connectivity

### Advanced Features
- **Scenario Upload**: Transfer waypoint paths to robots for autonomous navigation
- **Diagnostics**: Monitor battery, temperature, motor status, and errors
- **Packet-Level Control**: Low-level radio packet manipulation
- **Response Processing**: Parse status and diagnostic responses

---

## Hardware Requirements

- **Radio Module**: Connex 4490 serial radio transceiver
- **Connection**: USB-to-Serial adapter (or direct serial port)
- **Robots**: Compatible robotic vehicles with Connex 4490 receivers
- **Operating System**: Windows, Linux, or macOS with Python 3.7+

### Connex 4490 Specifications
- Baud Rate: 115200 (default)
- Serial Protocol: Binary packets with 7-byte headers
- RF Channels: 0-255 (commonly use 16, 26, 37)
- Max Payload: 80 bytes per packet

---

## Installation

### Prerequisites

```bash
pip install pyserial pynput
```

### Required Libraries
- `serial` (PySerial): Serial communication
- `pynput`: Keyboard input handling (optional, for manual control)
- `tkinter`: GUI support (built-in with Python)
- `struct`: Binary data packing/unpacking (built-in)
- `dataclasses`: Data structure definitions (built-in, Python 3.7+)

### Setup

1. Clone or download the code files
2. Connect your Connex 4490 module via USB
3. Identify the serial port (e.g., `COM9` on Windows, `/dev/ttyUSB0` on Linux)
4. Update the port in your script:

```python
radio = VRCM(port="COM9")  # Change to your port
```

---

## Quick Start

### Basic Robot Control

```python
from test import VRCM

# Initialize radio connection
radio = VRCM(port="COM9")

# Add a robot (serial number, client ID, response ID)
radio.add_bot(serial=1201, clientID=1, respID=1)

# Power on the robot
radio.power('on')

# Drive forward
radio.drive(x=0, y=100, z=0)  # y=100 is full forward

# Raise tower/torso
radio.toggle_tower('up')

# Power off
radio.power('off')

# Close connection
radio.close()
```

### Discovering Robots

```python
radio = VRCM(port="COM9")
radio.discover_robots()  # Scans all RF channels
print(radio.avalible_bots_dic)  # Shows found robots by channel
```

### Uploading a Path

```python
from tester import TPathForXmit, send_scenario_to_robot
from test import VRCM, THeader, TRadioPacket, PACKET_TYPES, TRespHeader

# Create waypoint path (x, y, flag)
waypoints = [
    (0.0, 0.0, 0),    # Start
    (10.0, 0.0, 0),   # East 10m
    (10.0, 10.0, 0),  # North 10m
    (0.0, 10.0, 0),   # West 10m
    (0.0, 0.0, 1),    # Return to start (flag=1 indicates end)
]

# Create path object
path = TPathForXmit.from_waypoints(
    name="Square",
    waypoints=waypoints,
    pathdate=241025,  # Oct 25, 2024 (YYMMDD)
    pathtime=143000   # 2:30 PM (HHMMSS)
)

# Upload to robot
radio = VRCM("COM9")
success = send_scenario_to_robot(
    radio=radio,
    path=path,
    client_id=1,
    THeader=THeader,
    TRadioPacket=TRadioPacket,
    PACKET_TYPES=PACKET_TYPES,
    TRespHeader=TRespHeader
)
```

---

## Architecture

### Class Hierarchy

```
Connex4490 (Base Radio Communication)
    ├── Radio packet send/receive
    ├── AT command mode control
    ├── RF channel management
    └── Low-level protocol handling

VRCM (Robot Control Manager) extends Connex4490
    ├── Robot database management
    ├── High-level control functions
    ├── Power management
    └── Movement commands
```

### Communication Flow

1. **Command Construction**: Create payload (e.g., `RCPayload`, `TOnOffSerialPayload`)
2. **Header Addition**: Wrap with `THeader` (client IDs, packet type, state)
3. **Radio Packaging**: Encapsulate in `TRadioPacket` (destination, retries)
4. **Serial Transmission**: Send via Connex 4490 module
5. **Response Handling**: Parse incoming `ResponsePayload_Status` or `ResponsePayload_Diag`

---

## Core Components

### Data Structures

#### THeader
4-byte header for all payloads:
```python
@dataclass
class THeader:
    respClient: int      # Which client should respond (0-15)
    activeClient: int    # Target client for command (0-15)
    ptype: int          # Packet type (0-15)
    state: int          # Robot state (0-15)
    cycle: int          # 16-bit cycle/parameter field
```

#### TRadioPacket
7-byte radio header + 80-byte payload:
```python
@dataclass
class TRadioPacket:
    cmd: int            # Command byte (0x81 = send, 0x82 = SDC)
    paylen: int         # Payload length (0-80)
    reserved: int       # Reserved byte
    retries: int        # Number of retries (0-15)
    dest1: int          # Destination address byte 1
    dest2: int          # Destination address byte 2
    dest3: int          # Destination address byte 3
    payload: bytes      # Up to 80 bytes
```

#### RCPayload
Remote control command payload:
```python
@dataclass
class RCPayload:
    hdr: THeader
    joyX: int           # -100 to 100 (left/right)
    joyY: int           # -100 to 100 (forward/back)
    joyZ: int           # -100 to 100 (rotation)
    btns: int           # Button bitfield
    hitThreshold: int   # Collision sensitivity
    hitTimeLimit: int   # Hit detection timeout
```

### Packet Types

```python
PACKET_TYPES = {
    "CONTROLLER_INPUT": 0,      # RC joystick commands
    "RADIO_POWER": 1,           # Change transmit power
    "NETWORK_POSITION": 2,      # Change client ID
    "SCENARIO_UPLOAD": 3,       # Begin scenario upload
    "RADIO_CHANNEL": 4,         # Change RF channel
    "SCENARIO_DNLOAD": 5,       # Download scenario packets
    "CLIENT_TURNONFF": 11,      # Power on/off
    "OTHER_COMMAND": 9,         # Miscellaneous commands
    "RESPONSE_PACK_STATUS": 16, # Status response
    "RESPONSE_PACK_DIAG": 17,   # Diagnostics response
}
```

### Robot States

```python
TSystemState = {
    "CCPU_STATE_INIT": 1,       # Initializing
    "CCPU_STATE_RC": 2,         # Remote control mode
    "CCPU_STATE_SCEN": 3,       # Scenario playback
    "CCPU_STATE_RECORD": 4,     # Recording path
    "CCPU_STATE_HITPAUSE": 5,   # Paused after collision
    "CCPU_STATE_LOWBATTERY": 6, # Low battery state
    "CCPU_STATE_FAULT": 7,      # Fault condition
    "CCPU_STATE_DO_NOTHING": 8, # Idle state
    "CCPU_STATE_ESTOP": 15,     # Emergency stop
}
```

---

## Usage Examples

### Example 1: Basic Movement Control

```python
radio = VRCM(port="COM9")
radio.add_bot(1201, 1, 1)
radio.power('on')

# Drive forward for 2 seconds
for _ in range(20):
    radio.drive(x=0, y=50, z=0)
    time.sleep(0.1)

# Turn right
for _ in range(20):
    radio.drive(x=0, y=0, z=50)
    time.sleep(0.1)

# Stop
radio.drive(x=0, y=0, z=0)
radio.power('off')
```

### Example 2: Multi-Robot Coordination

```python
radio = VRCM(port="COM9")

# Add multiple robots
radio.add_bot(1201, 1, 1)  # Robot A
radio.add_bot(1202, 2, 2)  # Robot B

# Control Robot A
radio.set_current_bot(0)
radio.power('on')
radio.drive(x=0, y=100, z=0)

# Switch to Robot B
radio.set_current_bot(1)
radio.power('on')
radio.drive(x=0, y=-100, z=0)
```

### Example 3: Changing RF Channel

```python
radio = VRCM(port="COM9")
radio.add_bot(1201, 1, 1)

# Move robot to channel B
radio.set_rf('B')           # Switch our radio to channel B
radio.change_bot_rf('B')    # Tell robot to switch to B

# Verify with ping
if radio.ping('B', 1, attempts=3):
    print("Robot successfully moved to channel B")
```

### Example 4: Retrieving Diagnostics

```python
from test import BuildAndSendRcPacket, EMPTY_JOYSTICK, ResponsePayload_Diag

radio = VRCM(port="COM9")
radio.add_bot(1201, 1, 1)

# Request diagnostic data
data = BuildAndSendRcPacket(
    radio=radio,
    destCli=1,
    respCli=1,
    cycle=6,  # Diagnostic request cycle
    joystick=EMPTY_JOYSTICK,
    packettype='OTHER_COMMAND',
    wait=0.5
)

# Parse response
if len(data) > 11 and data[11] == 17:  # Diag packet type
    diag = ResponsePayload_Diag.unpack(data[11:])
    print(f"Battery Voltage: {diag.vbat}")
    print(f"Battery Temps: {diag.btemp1}")
    print(f"Motor Temps: {diag.otemp}")
```

---

## Protocol Documentation

### RF Channel Mapping

| Channel Label | RF Channel Number |
|--------------|-------------------|
| A            | 16                |
| B            | 26                |
| C            | 37                |

### Joystick Value Ranges

- **X/Y/Z Axes**: -100 to +100
  - Negative values: left/backward/counter-clockwise
  - Positive values: right/forward/clockwise
  - Zero: stop

### Button Bitfield

```
Bit 0: Reserved
Bit 1: Tower Up (value=2)
Bit 2: Tower Down (value=4)
Bit 3: Tower Half (value=6)
Bits 4-7: Additional buttons
```

### AT Command Mode

The Connex 4490 supports configuration via AT commands:

```python
# Enter command mode
radio.send_command('enter_command_mode')  # Sends: AT+++\r

# Change channel
radio.send_command('change_channel', CHANNEL=26)

# Exit command mode
radio.send_command('exit_command_mode')  # Sends: CCATO\r
```

### Scenario Download Protocol

1. **Initiate**: Send first packet with checksum
2. **SDC Response**: Wait for 0x82 confirmation
3. **Request Loop**: Robot requests packets sequentially
4. **Send Requested**: Transmit requested packet with retries
5. **Completion**: Send closeout message with status=0xFF
6. **Final SDC**: Wait for termination confirmation

---

## Troubleshooting

### Connection Issues

**Problem**: `Serial connection failed`
- Verify correct COM port
- Check USB cable connection
- Ensure no other program is using the port
- Try different baud rates (57600, 115200, 230400)

**Problem**: `Radio not responding to commands`
- Enter command mode explicitly
- Check radio power supply
- Verify antenna connection
- Try soft reset: `radio.send_command('soft_reset')`

### Robot Control Issues

**Problem**: `Robot doesn't respond to commands`
- Verify robot is powered on
- Check RF channel match
- Confirm correct client ID
- Increase retry count in packets
- Reduce command frequency

**Problem**: `Power on/off fails`
- Verify correct serial number
- Ensure sufficient timeout (10+ seconds)
- Check robot battery level
- Try pinging first to verify connection

### Path Upload Issues

**Problem**: `Scenario upload times out`
- Increase timeout parameter (default: 10s → 30s)
- Reduce waypoint count if > 200 points
- Verify robot has free memory (format if needed)
- Check packet retries (increase to 10+)

**Problem**: `Checksum mismatch`
- Ensure waypoint coordinates are valid floats
- Verify path name is ≤ 12 characters
- Check date/time format (YYMMDD/HHMMSS)

---

## API Reference

### VRCM Class

#### Constructor
```python
VRCM(port: str, baudrate: int = 115200, timeout: float = 0.5)
```
Initialize radio connection.

#### Methods

##### `add_bot(serial: int, clientID: int, respID: int) -> bool`
Register a robot in the control system.

##### `power(state: str = 'on') -> bool`
Power current robot on or off. Returns success status.

##### `drive(x: int = 0, y: int = 0, z: int = 0)`
Send movement command with joystick values (-100 to 100).

##### `toggle_tower(position: str = 'up')`
Control tower/torso position. Options: 'up', 'down', 'half'.

##### `set_rf(channel: str = 'a')`
Switch radio to specified RF channel ('A', 'B', or 'C').

##### `change_bot_rf(channel: str = 'a')`
Command current robot to change its RF channel.

##### `change_bot_id(network_id: int = 8)`
Assign new client ID to current robot.

##### `discover_robots()`
Scan all RF channels for available robots. Updates `avalible_bots_dic`.

##### `ping(rf: str, client: int, attempts: int = 1) -> bool`
Test connectivity with specific robot on given channel.

### Connex4490 Class

#### `send_command(command_key: str, **kwargs) -> bytes`
Send AT command to radio module. See `CONNEX4490_COMMANDS` dict for options.

#### `send_packet(packet: TRadioPacket)`
Transmit raw radio packet.

#### `read_packet(timeout: float = 1) -> bytes`
Receive data from radio module.

#### `change_rf_channel(channel: int | str)`
Switch RF channel (accepts channel number or label 'A'/'B'/'C').

### Path Management Functions

#### `TPathForXmit.from_waypoints(...) -> TPathForXmit`
Create path object from waypoint list.

Parameters:
- `name`: Path identifier (max 12 chars)
- `waypoints`: List of (x, y, flag) tuples
- `lat0`, `lon0`: Origin coordinates
- `pathdate`: YYMMDD format (e.g., 241025)
- `pathtime`: HHMMSS format (e.g., 143000)

#### `send_scenario_to_robot(...) -> bool`
Upload complete path to robot with proper protocol handling.

---

## Safety Considerations

1. **Emergency Stop**: Always have a physical E-stop accessible
2. **Range Limits**: Keep robots within radio range (typically < 1km)
3. **Collision Avoidance**: Set appropriate `hitThreshold` values
4. **Battery Monitoring**: Check diagnostics regularly
5. **RF Interference**: Avoid operating near high-power transmitters

---

## Contributing

To extend this system:

1. **Add Packet Types**: Update `PACKET_TYPES` dict and create corresponding payload classes
2. **Custom Commands**: Implement new methods in `VRCM` class
3. **Enhanced Diagnostics**: Parse additional response payload fields
4. **GUI Development**: Create `tkinter` or web-based control interface

---

## License

This code is provided as-is for educational and research purposes. Verify compliance with local RF regulations when operating radio equipment.

---

## Changelog

### Version 1.0
- Initial release
- Core RC functionality
- Multi-robot support
- Path upload capability
- Diagnostic monitoring

---

## Support

For issues, questions, or feature requests, please refer to the troubleshooting section or review the inline code comments for detailed implementation notes.
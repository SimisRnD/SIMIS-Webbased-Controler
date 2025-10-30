from enum import IntEnum
import ctypes


class TPacketType(IntEnum):
    # Server (Master RC) to client, max 16 to fit in 4 bits
    CONTROLLER_INPUT     = 0
    RADIO_POWER          = 1
    NETWORK_POSITION     = 2
    SCENARIO_UPLOAD      = 3
    RADIO_CHANNEL        = 4
    SCENARIO_DNLOAD      = 5
    FORMAT_PACKET        = 6
    CPRO_STATUS_REQUEST  = 7
    GENERATE_PATH        = 8
    OTHER_COMMAND        = 9
    SCENARIO_SETACTIVE   = 10
    CLIENT_TURNONFF      = 11
    HD_SENSITIVITY       = 12
    SPEEDPACK            = 13
    GAINPACK             = 14
    SPDTYPE              = 15

    # Client to server, values 16–254
    RESPONSE_PACK_STATUS   = 16
    RESPONSE_PACK_DIAG     = 17
    RESPONSE_PACK_UPLOAD   = 18
    RESPONSE_PACK_ACK      = 19
    RESPONSE_PACK_MOTFLTS  = 20
    RESPONSE_PACK_PATHINV  = 21
    RESPONSE_PACK_PATHNAME = 22
    RESPONSE_PACK_DLREQU   = 23
    ERROR_DETAILS          = 24

NUM_CLIENTS = 8
COMM_PERF_SIZE = 20

class ClientData(ctypes.LittleEndianStructure):
    _fields_ = [
        ("clientId", ctypes.c_uint8),
        ("state", ctypes.c_uint8),
        ("lastState", ctypes.c_uint8),
        ("reportedState", ctypes.c_uint8),
        ("errorbits", ctypes.c_uint16),

        # Hit Detection
        ("hitThreshold", ctypes.c_uint8),
        ("hitTimeLimit", ctypes.c_uint8),
        ("HdSensitivity", ctypes.c_uint8),
        ("hitPauseTime", ctypes.c_uint8),
        ("hit_zone_data", ctypes.c_uint8),
        ("zonesEnable", ctypes.c_bool),
        ("accelEnable", ctypes.c_bool),
        ("hdEnable", ctypes.c_bool),

        # Sonar
        ("sonarsEnable", ctypes.c_bool),
        ("distanceThresh", ctypes.c_uint16),

        # Communications
        ("commPerf", ctypes.c_uint8 * COMM_PERF_SIZE),
        ("commPerfIdx", ctypes.c_uint8),
        ("gotPacketFlag", ctypes.c_uint8),

        ("pathName", ctypes.c_char * 12),

        # GPS
        ("utmX", ctypes.c_int32),
        ("utmY", ctypes.c_int32),
        ("utmZone", ctypes.c_char * 4),
        ("numSat1", ctypes.c_uint8),
        ("numSat2", ctypes.c_uint8),
        ("gpsFix1", ctypes.c_uint8),
        ("gpsFix2", ctypes.c_uint8),
        ("COG", ctypes.c_int8),
        ("speed", ctypes.c_uint8),
        ("motSpeed", ctypes.c_int8),
        ("flags", ctypes.c_uint8),
        ("rpm", ctypes.c_int16 * 4),

        # Speed and gain
        ("dSpeedWhole", ctypes.c_int16),
        ("dSpeedDec", ctypes.c_int16),
        ("gainWhole", ctypes.c_int16),
        ("gainDec", ctypes.c_int16),
        ("isSpeedTypeRec", ctypes.c_bool),

        # Battery
        ("bvolt", ctypes.c_uint16 * 2),
        ("bcap", ctypes.c_uint8 * 3),
        ("bcur", ctypes.c_int16 * 3),
        ("btemp1", ctypes.c_uint8 * 3),
        ("btemp2", ctypes.c_uint8 * 3),
        ("btemp3", ctypes.c_uint8 * 3),
        ("otemp", ctypes.c_uint8 * 5),
        ("fans", ctypes.c_uint16 * 5),

        # Messages
        ("msgSent", ctypes.c_uint16),
        ("msgRecv", ctypes.c_uint16),

        ("btnMapped", ctypes.c_int),
        ("serial", ctypes.c_uint16)
    ]

# Array of clients
clientList = (ClientData * NUM_CLIENTS)()


#[vertical (x), horizontal (y), twist (z), 
# x-nomalized, y-normalized, z-normalized, button-value]
JOYSTICK_STATE = [0,0,0,0,0,0,0]  # Normalized values are between -100,100

#Definition of Button states
RC_BTN      = 4
MENU_BTN    = 0
SHFT_BTN    = 8
SCEN_START  = 12
SCEN_STOP   = 13
REC_START   = 14
REC_STOP    = 15
RISER_UP    = 16
RISER_DOWN  = 11
CB_1        = 1
CB_2        = 2
CB_3        = 6
CB_4        = 3
CB_5        = 5
CB_6        = 9
CB_7        = 10
CB_8        = 7

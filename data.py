
import struct
from dataclasses import dataclass

PACKET_TYPES = {
    # Server (Master RC) to client, max 16 to fit in 4 bits
    "CONTROLLER_INPUT": 0,    # Controller inputs to be sent to the Core CPU
    "RADIO_POWER": 1,         # Request that a client change its radio power
    "NETWORK_POSITION": 2,    # Change the ID of the client
    "SCENARIO_UPLOAD": 3,     # Request to begin upload process
    "RADIO_CHANNEL": 4,       # Request client change its radios channel ID
    "SCENARIO_DNLOAD": 5,     # Packet downloading a scenario to the client
    "FORMAT_PACKET": 6,       # Packet used to request a memory format of client
    "CPRO_STATUS_REQUEST": 7, # Requests comm protocol status from client 
    "GENERATE_PATH": 8,       # Client generates a scen path, uses 'cycle' too
    "OTHER_COMMAND": 9,       # Additional commands as per 'cycle'
    "SCENARIO_SETACTIVE": 10,
    "CLIENT_TURNONFF": 11,    # cycle!=0 -> turn ON, cycle==0 -> turn OFF
    "HD_SENSITIVITY": 12,     # Adjust HD sensitivity, cycle = desired sensitivity
    "SPEEDPACK": 13,
    "GAINPACK": 14,
    "SPDTYPE": 15,            # Change speed type for scenario playback

    # Client to server packet types (values > 15, must fit in a byte)
    "RESPONSE_PACK_STATUS": 16,   # System status response packet
    "RESPONSE_PACK_DIAG": 17,     # Diagnostic response packet
    "RESPONSE_PACK_UPLOAD": 18,   # Client is uploading a scenario
    "RESPONSE_PACK_ACK": 19,      # Client acknowledges server command
    "RESPONSE_PACK_MOTFLTS": 20,  # Deliver motor fault counts
    "RESPONSE_PACK_PATHINV": 21,  # Delivery path inventory on client
    "RESPONSE_PACK_PATHNAME": 22,
    "RESPONSE_PACK_DLREQU": 23,   # Request download
    "ERROR_DETAILS": 24           # Get detailed error data from client
}

TSystemState = {
    "CCPU_STATE_INIT": 1,
    "CCPU_STATE_RC": 2,
    "CCPU_STATE_SCEN": 3,
    "CCPU_STATE_RECORD": 4,
    "CCPU_STATE_HITPAUSE": 5,
    "CCPU_STATE_LOWBATTERY": 6,
    "CCPU_STATE_FAULT": 7,
    "CCPU_STATE_DO_NOTHING": 8,
    "CCPU_STATE_OBSTACLE": 9,
    "CCPU_STATE_POST_BOOT": 10,   # Upon boot - nothing is running yet
    "CCPU_STATE_PRE_INIT": 11,    # Waiting for 'ON' signal from radio
    "CCPU_STATE_PRE_OFF": 12,     # Radio sets this before turning off
    "CCPU_STATE_FORM_L": 13,      # Leader in formation
    "CCPU_STATE_FORM_F": 14,      # Follower in formation

    "CCPU_STATE_ESTOP": 15,
    "CCPU_STATE_INVALID": 255
}


@dataclass
class TRadioPacket:
    cmd: int
    paylen: int
    reserved: int
    retries: int
    dest1: int
    dest2: int
    dest3: int
    payload: bytes

    def pack(self) -> bytes:
        header = struct.pack("<BBBBBBB",
                             self.cmd,
                             self.paylen,
                             self.reserved,
                             self.retries,
                             self.dest1,
                             self.dest2,
                             self.dest3)
        payload_fixed = self.payload.ljust(80, b"\x00")
        return header + payload_fixed

@dataclass
class THeader:
    respClient: int
    activeClient: int
    ptype: int
    state: int
    cycle: int

    def pack(self) -> bytes:
        byte1 = (self.activeClient << 4) | (self.respClient & 0x0F)
        byte2 = (self.state << 4) | (self.ptype & 0x0F)
        return struct.pack("<BBH", byte1, byte2, self.cycle)

    @classmethod
    def unpack(cls, data: bytes):
        byte1, byte2, cycle = struct.unpack("<BBH", data[:4])
        respClient = byte1 & 0x0F
        activeClient = (byte1 >> 4) & 0x0F
        ptype = byte2 & 0x0F
        state = (byte2 >> 4) & 0x0F
        return cls(respClient, activeClient, ptype, state, cycle)
    
@dataclass
class TOnOffSerialPayload:
    hdr: THeader
    serial: int

    def pack(self) -> bytes:
        return self.hdr.pack() + struct.pack("<H", self.serial)

    @classmethod
    def unpack(cls, data: bytes):
        hdr = THeader.unpack(data[:4])
        serial, = struct.unpack("<H", data[4:6])
        return cls(hdr, serial)


def onoff_packet(serial,clientID,power=True):
    #First Generate header
    if power:
        cycle = 1
    else:
        cycle = 0
    hdr = THeader(respClient=clientID,
                  activeClient=clientID,
                  ptype=PACKET_TYPES["CLIENT_TURNONFF"],
                  state=TSystemState["CCPU_STATE_DO_NOTHING"],
                  cycle=cycle
                  )
    payload = TOnOffSerialPayload(hdr,serial).pack()
    full_packet = TRadioPacket(cmd=0x81,
                               paylen=len(payload),
                               reserved=0,
                               retries=5,
                               dest1=0xFF,
                               dest2=0xFF,
                               dest3=0xFF,
                               payload=payload)
    
    print(full_packet.pack())


onoff_packet(1202,3,True)
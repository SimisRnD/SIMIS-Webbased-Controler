import serial
import time
from dataclasses import dataclass
import struct

import struct
from dataclasses import dataclass
import tkinter as tk
from functools import partial
import logging

TORSO = {None:0,
         'up':2,
         'down':4,
         'half':6}

import struct
from dataclasses import dataclass

@dataclass
class ResponsePayload_Status:
    packetType: int
    clientId: int
    state: int
    errors: int
    serial: int
    utmX: int
    utmY: int
    COG: int
    gpsInfo: int
    gpsInfo2: int
    speed: int
    flags: int
    rpm: tuple
    motErrors: tuple
    motspeed: int
    hit_zone: int
    utmZone: str

    @classmethod
    def unpack(cls, data: bytes):
        fmt = "<BBHHiihBBbB4h8BbB4s"
        size = struct.calcsize(fmt)
        fields = struct.unpack(fmt, data[:size])

        client_state_byte = fields[1]
        clientId = client_state_byte & 0x0F
        state = (client_state_byte >> 4) & 0x0F

        return cls(
            packetType=fields[0],
            clientId=clientId,
            state=state,
            errors=fields[2],
            serial=fields[3],
            utmX=fields[4],
            utmY=fields[5],
            COG=fields[6],
            gpsInfo=fields[7],
            gpsInfo2=fields[8],
            speed=fields[9],
            flags=fields[10],
            rpm=fields[11:15],
            motErrors=fields[15:23],
            motspeed=fields[23],
            hit_zone=fields[24],
            utmZone=fields[25].decode(errors="ignore").strip("\x00")
        )

from dataclasses import dataclass
import struct

@dataclass
class ResponsePayload_Diag:
    packetType: int
    clientId: int
    state: int
    cycle: int
    serial: int
    ibat: tuple
    vbat: tuple
    bcap: tuple
    btemp1: tuple
    btemp2: tuple
    btemp3: tuple
    otemp: tuple
    fans: tuple

    @classmethod
    def unpack(cls, data: bytes):
        fmt = "<BBHH3h3B3B3B3B3B5B5H"
        size = struct.calcsize(fmt)
        fields = struct.unpack(fmt, data[:size])

        # Split clientId/state from second byte
        client_byte = fields[1]
        clientId = client_byte & 0x0F
        state = (client_byte >> 4) & 0x0F

        return cls(
            packetType=fields[0],
            clientId=clientId,
            state=state,
            cycle=fields[2],
            serial=fields[3],
            ibat=fields[4:7],
            vbat=fields[7:10],
            bcap=fields[10:13],
            btemp1=fields[13:16],
            btemp2=fields[16:19],
            btemp3=fields[19:22],
            otemp=fields[22:27],
            fans=fields[27:32],
        )


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


CONNEX4490_COMMANDS = {
    'enter_command_mode': {
        'command': [0x41, 0x54, 0x2B, 0x2B, 0x2B, 0x0D],  # AT+++\r
        'expected_response': [0xCC, 0x43, 0x4F, 0x4D],      # CCOM
        'response_map': {
            (0xCC, 0x43, 0x4F, 0x4D): "Successfully entered command mode"
        },
        'description': "Enter AT Command Mode"
    },
    
    'exit_command_mode': {
        'command': [0xCC, 0x41, 0x54, 0x4F, 0x0D],          # CCATO\r
        'expected_response': [0xCC, 0x44, 0x41, 0x54],      # CDAT
        'response_map': {
            (0xCC, 0x44, 0x41, 0x54): "Successfully exited command mode"
        },
        'description': "Exit AT Command Mode"
    },
    
    'status_request': {
        'command': [0xCC, 0x00, 0x00],
        'expected_response': 'dynamic',  # Response varies based on status
        'response_map': {
            'status_codes': {
                0x00: "Server mode",
                0x01: "Client in range",
                0x03: "Out of range"
            }
        },
        'description': "Get radio status and firmware version",
        'response_format': "[0xCC, firmware_version, status_code]"
    },
    
    'change_channel': {
        'command': [0xCC, 0x02, 'CHANNEL'],  # CHANNEL = 0-255
        'expected_response': [0xCC, 'CHANNEL'],
        'response_map': {
            'success': "Successfully changed to channel {channel}"
        },
        'description': "Change RF channel (0-255)",
        'parameters': ['channel (0-255)']
    },
    
    'change_role': {
        'command': [0xCC, 0x03, 'ROLE'],  # 0x00=Server, 0x03=Client
        'expected_response': [0xCC, 'FW_VERSION', 'ROLE'],
        'response_map': {
            'role_codes': {
                0x00: "Server mode",
                0x03: "Client mode"
            }
        },
        'description': "Set radio role (Server/Client)",
        'parameters': ['role (0x00=Server, 0x03=Client)']
    },
    
    'change_sync_channel': {
        'command': [0xCC, 0x05, 'SYNC_CHANNEL'],  # 0-255
        'expected_response': [0xCC, 'SYNC_CHANNEL'],
        'response_map': {
            'success': "Successfully changed sync channel to {sync_channel}"
        },
        'description': "Change synchronization channel (0-255)",
        'parameters': ['sync_channel (0-255)']
    },
    
    'sleep_wake_up': {
        'command': [0xCC, 0x07],
        'expected_response': [0xCC, 'CHANNEL'],
        'response_map': {
            'success': "Radio woken up successfully"
        },
        'description': "Wake up radio from sleep mode"
    },
    
    'broadcast_packets': {
        'command': [0xCC, 0x08, 'PACKET_TYPE'],  # 0x00=Addressed, 0x01=Broadcast
        'expected_response': [0xCC],
        'response_map': {
            'packet_types': {
                0x00: "Addressed packets enabled",
                0x01: "Broadcast packets enabled"
            }
        },
        'description': "Configure broadcast packet settings",
        'parameters': ['packet_type (0x00=Addressed, 0x01=Broadcast)']
    },
    
    'write_destination_address': {
        'command': [0xCC, 0x10, 'BYTE_0', 'BYTE_1', 'BYTE_2', 'BYTE_3', 'BYTE_4', 'BYTE_5'],
        'expected_response': [0xCC, 'BYTE_0', 'BYTE_1', 'BYTE_2', 'BYTE_3', 'BYTE_4', 'BYTE_5'],
        'response_map': {
            'success': "Destination address set to: {address_hex}"
        },
        'description': "Write 6-byte destination address",
        'parameters': ['6 address bytes']
    },
    
    'read_destination_address': {
        'command': [0xCC, 0x11],
        'expected_response': [0xCC, 'BYTE_0', 'BYTE_1', 'BYTE_2', 'BYTE_3', 'BYTE_4', 'BYTE_5'],
        'response_map': {
            'success': "Current destination address: {address_hex}"
        },
        'description': "Read current destination address"
    },
    
    'force_calibration': {
        'command': [0xCC, 0x12, 0x00, 0x00],
        'expected_response': [0xCC, 'FW_VERSION', 'OPERATION_STATUS'],
        'response_map': {
            'operation_status': {
                0x00: "Normal operation",
                0x01: "Client in normal operation", 
                0x02: "Server in acquisition sync",
                0x03: "Normal operation"
            }
        },
        'description': "Force radio calibration"
    },
    
    'auto_destination': {
        'command': [0xCC, 0x15],
        'expected_response': [0xCC],
        'response_map': {
            'success': "Auto destination enabled"
        },
        'description': "Enable auto destination"
    },
    
    'read_digital_inputs': {
        'command': [0xCC, 0x20],
        'expected_response': [0xCC, 'INPUT_STATE'],
        'response_map': {
            'success': "Digital inputs state: 0x{input_state:02X}"
        },
        'description': "Read digital input pins state"
    },
    
    'read_adc': {
        'command': [0xCC, 0x21],
        'expected_response': [0xCC, 'ADC_VALUE'],
        'response_map': {
            'success': "ADC reading: {adc_value} (LSB of 10-bit ADC)"
        },
        'description': "Read ADC value"
    },
    
    'report_rssi': {
        'command': [0xCC, 0x22],
        'expected_response': [0xCC, 'RSSI'],
        'response_map': {
            'success': "RSSI: {rssi} dBm"
        },
        'description': "Report last valid RSSI"
    },
    
    'write_digital_outputs': {
        'command': [0xCC, 0x23, 'OUTPUT_STATE'],  # 0-255
        'expected_response': [0xCC, 'OUTPUT_STATE'],
        'response_map': {
            'success': "Digital outputs set to: 0x{output_state:02X}"
        },
        'description': "Write digital output pins",
        'parameters': ['output_state (0-255)']
    },
    
    'write_dac': {
        'command': [0xCC, 0x24, 'DAC_VALUE'],  # 0-255
        'expected_response': [0xCC, 'DAC_VALUE'],
        'response_map': {
            'success': "DAC set to: {dac_value}"
        },
        'description': "Write DAC value",
        'parameters': ['dac_value (0-255)']
    },
    
    'set_max_power': {
        'command': [0xCC, 0x25, 'POWER_LEVEL'],  # 0-255
        'expected_response': [0xCC, 'MAX_POWER'],
        'response_map': {
            'success': "Max power set to: {max_power}"
        },
        'description': "Set maximum transmission power",
        'parameters': ['power_level (0-255)']
    },
    
    'report_last_packet_rssi': {
        'command': [0xCC, 0x26],
        'expected_response': [0xCC, 'RSSI'],
        'response_map': {
            'success': "Last packet RSSI: {rssi} dBm"
        },
        'description': "Report RSSI of last received packet"
    },
    
    'set_range_mode': {
        'command': [0xCC, 0x27, 'RANGE_MODE'],  # 0x00=Normal, 0x01=Long Range
        'expected_response': [0xCC, 'RANGE_MODE'],
        'response_map': {
            'range_modes': {
                0x00: "Normal range mode enabled",
                0x01: "Long range mode enabled"
            }
        },
        'description': "Set range mode (Normal/Long Range)",
        'parameters': ['range_mode (0x00=Normal, 0x01=Long Range)']
    },
    
    'transmit_buffer_empty': {
        'command': [0xCC, 0x30],
        'expected_response': [0xCC, 'BUFFER_STATUS'],
        'response_map': {
            'buffer_status': {
                0x00: "Transmit buffer has data",
                0x01: "Transmit buffer is empty"
            }
        },
        'description': "Check if transmit buffer is empty"
    },
    
    'disable_sync_to_channel': {
        'command': [0xCC, 0x35],
        'expected_response': [0xCC, 'CHANNEL'],
        'response_map': {
            'success': "Sync to channel disabled"
        },
        'description': "Disable synchronization to channel"
    },
    
    'deep_sleep_mode': {
        'command': [0xCC, 0x86],
        'expected_response': [0xCC, 'CHANNEL'],
        'response_map': {
            'success': "Entering deep sleep mode"
        },
        'description': "Enter deep sleep mode"
    },
    
    'enter_probe': {
        'command': [0xCC, 0x8E, 'PROBE_MODE'],  # 0x00=Enter, 0x01=Exit
        'expected_response': [0xCC, 'PROBE_STATUS'],
        'response_map': {
            'probe_modes': {
                0x00: "Entered probe mode",
                0x01: "Exited probe mode"
            }
        },
        'description': "Enter/Exit probe mode",
        'parameters': ['probe_mode (0x00=Enter, 0x01=Exit)']
    },
    
    'read_temperature': {
        'command': [0xCC, 0xA4],
        'expected_response': [0xCC, 'TEMP_C'],
        'response_map': {
            'success': "Temperature: {temp}°C"
        },
        'description': "Read internal temperature sensor"
    },
    
    'read_supply_voltage': {
        'command': [0xCC, 0xA5],
        'expected_response': [0xCC, 'VOLTAGE'],
        'response_map': {
            'success': "Supply voltage: {voltage}V"  # voltage * 0.1 for actual volts
        },
        'description': "Read supply voltage (multiply by 0.1 for volts)"
    },
    
    'eeprom_read': {
        'command': [0xCC, 0xC0, 'START_ADDRESS', 'LENGTH'],
        'expected_response': [0xCC, 'LENGTH', 'DATA...'],
        'response_map': {
            'success': "EEPROM data: {data_hex}"
        },
        'description': "Read EEPROM data",
        'parameters': ['start_address (0-255)', 'length (1-255)']
    },
    
    'eeprom_write': {
        'command': [0xCC, 0xC1, 'START_ADDRESS', 'LENGTH', 'DATA...'],
        'expected_response': [0xCC, 'START_ADDRESS', 'LENGTH'],
        'response_map': {
            'success': "EEPROM written at address {address}: {data_hex}"
        },
        'description': "Write EEPROM data",
        'parameters': ['start_address (0-255)', 'length (1-255)', 'data_bytes...']
    },
    
    'soft_reset': {
        'command': [0xCC, 0xFF],
        'expected_response': [0xCC],
        'response_map': {
            'success': "Soft reset completed successfully"
        },
        'description': "Perform soft reset"
    }
}

# ----------------------------
# Radio packet definitions
# ----------------------------
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

    @classmethod
    def unpack(cls, data: bytes):
        fields = struct.unpack("<BBBBBBB", data[:7])
        payload = data[7:87]
        return cls(*fields, payload)


@dataclass
class ResponsePacket:
    packettype: int
    clientID: int
    state: int
    error: int
    

    def pack(self) -> bytes:
        header = struct.pack("<BBBB",
                             self.packettype,
                             self.clientID,
                             self.state,
                             self.error)
        
        return header

    @classmethod
    def unpack(cls, data: bytes):
        fields = struct.unpack("<BBBB", data[:4])
        
        return cls(*fields)


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
class TJoystick:
    x: int   # raw 16-bit
    y: int
    z: int
    xa: int  # adjusted -100 to 100
    ya: int
    za: int
    btn: int # 8-bit

EMPTY_JOYSTICK = TJoystick(0,0,0,0,0,0,0)
@dataclass
class RCPayload:
    hdr: THeader
    joyX: int
    joyY: int
    joyZ: int
    btns: int
    hitThreshold: int
    hitTimeLimit: int

    def pack(self) -> bytes:
        return (
            self.hdr.pack() +
            struct.pack("<bbbBBB",
                        self.joyX,
                        self.joyY,
                        self.joyZ,
                        self.btns,
                        self.hitThreshold,
                        self.hitTimeLimit)
        )

    @classmethod
    def unpack(cls, data: bytes):
        hdr = THeader.unpack(data[:4])
        joyX, joyY, joyZ, btns, hitThreshold, hitTimeLimit = struct.unpack("<bbbBBB", data[4:10])
        return cls(hdr, joyX, joyY, joyZ, btns, hitThreshold, hitTimeLimit)


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

@dataclass
class TDiscoverRobotsPayload:
    hdr: THeader
    
    def pack(self):
        return self.hdr.pack()

# ----------------------------
# Connex4490 class
# ----------------------------
class Connex4490:
    CHANNELS = {
    16: 'A',
    26: 'B',
    37: 'C'
}
    CHANNELS_r = {'A':16,'B':26,'C':37}
    def __init__(self, port, baudrate=115200, timeout=0.5):
        self.ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        if not self.ser.is_open:
            self.ser.open()
        print(f"Connected to {port} at {baudrate} baud.")
        self.avalible_bots_dic = {'A':[],'B':[],'C':[]}
    
    def add_avalable_bot(self,rf,id):
        if id not in self.avalible_bots_dic[rf]:
            self.avalible_bots_dic[rf].append(id)

    def send_command(self, command_key, **kwargs):
        """
        Send a command defined in CONNEX4490_COMMANDS.
        kwargs are substituted for parameters like CHANNEL, ROLE, etc.
        """
        cmd_def = CONNEX4490_COMMANDS[command_key]
        cmd_bytes = []
        for b in cmd_def['command']:
            if isinstance(b, str):
                if b in kwargs:
                    cmd_bytes.append(kwargs[b])
                else:
                    raise ValueError(f"Missing parameter {b} for command {command_key}")
            else:
                cmd_bytes.append(b)

        self.ser.write(bytearray(cmd_bytes))
        #print(f"Sent {command_key}: {[hex(b) for b in cmd_bytes]}")

        # Read response
        time.sleep(0.05)
        resp = self.ser.readline()
       

        # Map response
        response_map = cmd_def.get('response_map', {})
        if resp and response_map:
            resp_tuple = tuple(resp[:len(resp)])
            if resp_tuple in response_map:
                print(response_map[resp_tuple])
        return resp

    def send_packet(self, packet: TRadioPacket):
        data = packet.pack()[:7 + packet.paylen]
        self.ser.write(data)
        #print(f"--> Sent {len(data)} bytes, cmd=0x{packet.cmd:02X}")
        #print(f"Raw Packet: {bytearray(data)}")
        formated = str([hex(i).upper() for i in data]).replace('\', ',' ').replace('\'',' ')
        print(formated)

    def read_packet(self, timeout=1):
        self.ser.timeout = timeout
        
        data = self.ser.readline()
            
        if data != b'':
            #print(data)
            return data#ResponsePacket.unpack(data)
        return None
    def change_rf_channel(self,channel):
        '''
        channel (int or str):   Directlt input the desired RF channle (int) or
                                or the channel lable "A","B","C" caps insensitive '''
        if type(channel) == str:
            channel = self.CHANNELS_r[channel.upper()]

        self.send_command('enter_command_mode')
        self.send_command('change_channel',CHANNEL=channel)
        self.send_command('exit_command_mode')

    def radio_loop_timed_multi_command(self, ofp, time_ms=1800, retries=5):
        payload = ofp.pack()
        p = TRadioPacket(
            cmd=0x81,
            paylen=len(payload),
            reserved=0,
            retries=retries,
            dest1=0xFF,
            dest2=0xFF,
            dest3=0xFF,
            payload=payload
        )
        #print('Radio loop')
        # Delay based on packet type
        if ofp.hdr.ptype == 11:
            time.sleep(0.1)
        else:
            time.sleep(0.01)

       
        self.send_packet(p)
           
            
        # Wait for first SDC packet (cmd=0x82)
        sdc = self.read_packet(timeout=1.0)
        # if not sdc or sdc[0]!= 0x82:
        #     #print("  ****** ERROR 1 - SDC timeout")
        #     #return False
        # print("SDC Received")
        
        if len(sdc) > 5:
            print(sdc[5:])
            return True
        # Wait for client response (cmd=0x81)
        resp = self.read_packet(timeout=0.2)
        if not resp:
            # print(resp)
            # print("  ON OFF Transaction: client timeout")
            return False
            
        return True
        # if resp.cmd != 0x81:
        #     print(f"  Error: expected 0x81 packet but got 0x{resp.cmd:02X}")
        #     return False
        # else:
        #     print("====> Success", resp)
        #     return True
        
        

    def close(self):
        self.ser.close()
        print("Serial connection closed.")
    
    def discover_robots(self):

        clients = {1:False,2:False,
                   3:False,4:False,
                   5:False,6:False,
                   7:False,8:False,}
        
        for RF in self.CHANNELS:
            self.change_rf_channel(RF)
            for client in clients:
                for i in range(0,2):
                    hdr = THeader(respClient=client, 
                                  activeClient=client, 
                                ptype=PACKET_TYPES['OTHER_COMMAND'],
                                  state=TSystemState['CCPU_STATE_DO_NOTHING'],
                                    cycle=4)
                    ofp = TOnOffSerialPayload(hdr=hdr, serial=1201)
                    success = radio.radio_loop_timed_multi_command(ofp, time_ms=1800,retries=5)
                    time.sleep(0.2)
                    
                    if success:
                        self.add_avalable_bot(self.CHANNELS[RF],client)
                # print("ON/OFF Result:", clients)
        print(self.avalible_bots_dic)

    def ping(self,rf,client,attempts=1):
        self.change_rf_channel(rf)
        for i in range(attempts):
            time.sleep(1)
            hdr = THeader(respClient=client, 
                                    activeClient=client, 
                                    ptype=PACKET_TYPES['OTHER_COMMAND'],
                                    state=TSystemState['CCPU_STATE_DO_NOTHING'],
                                        cycle=4)
            ofp = TOnOffSerialPayload(hdr=hdr, serial=1201)
            success = radio.radio_loop_timed_multi_command(ofp, time_ms=1800,retries=10)
            if success:
                self.add_avalable_bot(self.CHANNELS[self.CHANNELS_r[rf]],client)
                return True

    def power_bot(self,serial:int,on:bool,rf,client=1,timeout=None):
        if on:
            desird_state = 'On'
            cycle = 1
        else:
            desird_state = 'Off'
            cycle = 0
        #self.change_rf_channel(rf)
        timer = time.time()
        while True:
            time.sleep(1)
            hdr = THeader(respClient=client, 
                            activeClient=client, 
                        ptype=PACKET_TYPES["CLIENT_TURNONFF"], 
                        state=TSystemState['CCPU_STATE_DO_NOTHING'], 
                        cycle=cycle)
            ofp = TOnOffSerialPayload(hdr=hdr, serial=serial)
            success = radio.radio_loop_timed_multi_command(ofp, time_ms=1800,retries=6)
            if success:
                print(serial, ': Powered',desird_state)
                return True
            
            if timeout:
                if time.time() - timer > timeout:
                    break
        print(f'{serial}: Failed to power {desird_state}.')
        return False
    def listen(self):
        while True:
            self.ser.timeout = 0.5
            value  = self.ser.readline()
            if value:
                print(value)

def BuildAndSendRcPacket(radio: Connex4490, destCli: int, respCli: int, cycle: int,
                         joystick: TJoystick, g_menuMode=False,packettype="CONTROLLER_INPUT",
                         retries=1,wait=None):
    # Build header
    hdr = THeader(
        respClient=respCli,
        activeClient=destCli,
        ptype=PACKET_TYPES[packettype],
        state=TSystemState["CCPU_STATE_RC"],
        cycle=cycle
    )

    # # Handle "noMove" logic
    # if joystick.btn:
    #     noMove = 15
    # else:
    #     noMove = max(0, getattr(BuildAndSendRcPacket, "noMove", 0) - 1)
    # BuildAndSendRcPacket.noMove = noMove  # persist like C's static variable

    if g_menuMode:
        joyX, joyY, joyZ = 0, 0, 0
        btns = 0
    else:
        joyX, joyY, joyZ = joystick.xa, joystick.ya, joystick.za
        btns = joystick.btn
        # Example button mapping (you’ll need to implement IsClicked() equivalents)
        # btns |= (is_clicked("RISER_UP")   << 1)
        # btns |= (is_clicked("RISER_DOWN") << 2)
        # btns |= (is_clicked("SHFT_BTN")   << 3)

    # Build payload
    rc_payload = RCPayload(
        hdr=hdr,
        joyX=joyX,
        joyY=joyY,
        joyZ=joyZ,
        btns=btns,
        hitThreshold=5,
        hitTimeLimit=5
    )

    payload_bytes = rc_payload.pack()

    # Build radio packet
    packet = TRadioPacket(
        cmd=0x81,
        paylen=len(payload_bytes),
        reserved=0,
        retries=retries,
        dest1=0xFF,
        dest2=0xFF,
        dest3=0xFF,
        payload=payload_bytes
    )

    # Send via radio
    radio.send_packet(packet)
    if wait:
        time.sleep(wait)
    data = radio.read_packet(1)

    n = 0
    while True:
        newdata = radio.read_packet(1)
        if newdata:
            data += newdata
        else:
            break
    return data

    #radio.read_packet(1)

    # # Update diagnostics like in C (you'll need to implement clientData objects)
    # pC = clientList[respCli-1]
    # pC.msgSent += 1
    # pC.commPerf[pC.commPerfIdx] = 1 if pC.gotPacketFlag else 0
    # pC.gotPacketFlag = False
    # pC.commPerfIdx = (pC.commPerfIdx + 1) % len(pC.commPerf)
    # if pC.msgSent > 9999:
    #     pC.msgSent = 0
    #     pC.msgRecv = 0



class VRCM(Connex4490):
    def __init__(self, port, baudrate=115200, timeout=0.5):
        super().__init__(port, baudrate, timeout)

        self.channel = 'A'
        self.bots = []
        self.current = None

        self.change_rf_channel(self.channel)
    
    def power(self,state='on'):
        
        state = state.lower()
        if state == 'on':
            power = True
        else:
            power = False
        
        #print('hey')
        serialNumber = self.bots[self.current]['serial number']
        clientID = self.bots[self.current]['client ID']
        print(f'Powering {state}: {serialNumber}')
        on = self.power_bot(serial=serialNumber,
                       on=power,
                       rf=self.channel,
                       client=clientID,
                       timeout=10) # 5 seconds was too short
        return on
    
    def add_bot(self,serial,clientID,respID):
        
        self.bots.append({'serial number':int(serial),
                          'client ID':int(clientID),
                          'response ID':int(respID)})
        self.current = len(self.bots)-1

        return True
        # for i in ['a','b','c']:
        #     print(i)
        #     isConnected = self.power()
        #     print('passed power')
        #     if isConnected:
                
        #         self.bots[self.current]['rf']=i.upper()
        #         return True
        # else:
        #     return False

    def send_physical_commands(self,joystick):
        bot = self.bots[self.current]
        clientID = bot['client ID']
        responseID = bot['response ID']
        # bot_rf = bot['rf']
        # if bot_rf != self.channel:
        #     self.change_rf_channel(bot_rf)
        BuildAndSendRcPacket(radio,clientID,responseID,0,joystick)

    def drive(self,x=0,y=0,z=0):
        joystick = TJoystick(x,y,z,x,y,z,0)
        print('Drive Damn it')
        self.send_physical_commands(joystick)

    def toggle_tower(self,position='up'):
        tower_pos = {'up':2,'down':4,'half':6}
        pos = tower_pos.get(position,0)
        joystick = TJoystick(0,0,0,0,0,0,pos)
        self.send_physical_commands(joystick)
    
    def avalible_bots(self):
        return self.bots
    
    def set_current_bot(self,i):
        self.current = i
    
    def set_rf(self,channel='a'):
        self.channel = channel.upper()
        self.change_rf_channel(channel)
    
    def change_bot_rf(self,channel='a'):
        channel_number = self.CHANNELS_r[channel.upper()]
        bot = self.bots[self.current]
        cliID = bot['client ID']
        respID = bot['response ID']
        joystick = TJoystick(0,0,0,0,0,0,0)
        BuildAndSendRcPacket(self,cliID, respID,channel_number, joystick, packettype="RADIO_CHANNEL", retries=3)
    
    def change_bot_id(self,network_id = 8):
        
        bot = self.bots[self.current]
        cliID = bot['client ID']
        respID = bot['response ID']
        joystick = TJoystick(0,0,0,0,0,0,0)
        BuildAndSendRcPacket(self,cliID, respID,network_id, joystick, packettype="NETWORK_POSITION", retries=2)
        self.bots[self.current]['client ID'] = network_id
        self.bots[self.current]['response ID'] = network_id



    



        



from pynput import keyboard
POS = 0
def check_arrows():
    
    def on_press(key):
        global POS
        if key == keyboard.Key.up:
            joystick = TJoystick(x=0, y=100, z=0,
                    xa=0, ya=100, za=0, btn=POS)
            BuildAndSendRcPacket(radio,3,3,0,joystick)
        elif key == keyboard.Key.down:
            joystick = TJoystick(x=0, y=-100, z=0,
                    xa=0, ya=-100, za=0, btn=POS)
            BuildAndSendRcPacket(radio,3,3,0,joystick)
        elif key == keyboard.Key.left:
            joystick = TJoystick(x=-100, y=0, z=0,
                    xa=-100, ya=0, za=0, btn=POS)
            BuildAndSendRcPacket(radio,3,3,0,joystick)
        elif key == keyboard.Key.right:
            joystick = TJoystick(x=100, y=0, z=0,
                    xa=100, ya=0, za=0, btn=POS)
            BuildAndSendRcPacket(radio,3,3,0,joystick)
        elif key == keyboard.Key.space:
            POS+=2
            POS = POS%6
            joystick = TJoystick(x=0, y=0, z=0,
                    xa=0, ya=0, za=0, btn=POS)
            BuildAndSendRcPacket(radio,3,3,0,joystick)
        else:
            joystick = TJoystick(x=0, y=0, z=0,
                    xa=0, ya=0, za=0, btn=0)
            BuildAndSendRcPacket(radio,3,3,0,joystick)

        
        
        

    # Create a listener that runs until you stop it with Ctrl+C
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()


# Example joystick object to send with packets
joystick = TJoystick(x=0, y=0, z=0, xa=0, ya=0, za=0, btn=0)

def send_move(radio, direction):
    """Send a joystick movement based on button press."""
    if direction == "up":
        joystick.ya = 50
        joystick.xa = 0
    elif direction == "down":
        joystick.ya = -50
        joystick.xa = 0
    elif direction == "left":
        joystick.xa = -50
        joystick.ya = 0
    elif direction == "right":
        joystick.xa = 50
        joystick.ya = 0
    elif direction == 'UP':
        joystick.btn = 2
        joystick.xa = 0
        joystick.ya = 0
    elif direction == 'DOWN':
        joystick.btn = 4
        joystick.xa = 0
        joystick.ya = 0
    else:
        joystick.xa = 0
        joystick.ya = 0


#     print(f"Sending move {direction} -> xa={joystick.xa}, ya={joystick.ya}")
#     BuildAndSendRcPacket(radio, destCli=1, respCli=1, cycle=1, joystick=joystick)

# def toggle_power(radio, serial, rf, on=True):
#     """Send a power on/off command."""
#     result = radio.power_bot(serial=serial, on=on, rf=rf, client=1, timeout=3)
#     print("Power result:", result)

# def build_gui(radio):
#     root = tk.Tk()
#     root.title("RC Controller")

#     # Movement buttons
#     tk.Button(root, text="↑", width=5, height=2,
#               command=partial(send_move, radio, "up")).grid(row=0, column=1)

#     tk.Button(root, text="←", width=5, height=2,
#               command=partial(send_move, radio, "left")).grid(row=1, column=0)

#     tk.Button(root, text="→", width=5, height=2,
#               command=partial(send_move, radio, "right")).grid(row=1, column=2)

#     tk.Button(root, text="↓", width=5, height=2,
#               command=partial(send_move, radio, "down")).grid(row=2, column=1)

#     # Stop button
#     tk.Button(root, text="Stop", width=5, height=2,
#               command=partial(send_move, radio, "stop")).grid(row=1, column=1)
    

#     tk.Button(root, text="TORSO UP", width=12, height=2,
#               command=partial(send_move, radio, "UP")).grid(row=3, column=0, pady=10)
#     tk.Button(root, text="TORSO DOWN", width=12, height=2,
#               command=partial(send_move, radio, "DOWN")).grid(row=3, column=2, pady=10)
    
#     # Power controls
#     tk.Button(root, text="Power ON", width=10,
#               command=partial(toggle_power, radio, 1201, 'A', True)).grid(row=4, column=0, pady=10)

#     tk.Button(root, text="Power OFF", width=10,
#               command=partial(toggle_power, radio, 1201, 'A', False)).grid(row=4, column=2, pady=10)

#     root.mainloop()

# ----------------------------
# Example usage
# ----------------------------
def identify_packet(data: bytes):
    if len(data) < 8:
        return None, None
    print(data)
    print(data.hex())
    # n = 0
    # for i in data:
    #     print(n,i)
    #     n+=1
    if 17 == data[11]:
        # Likely ResponsePayload_Status
        return "STATUS", data
    elif 16 ==  data[11]:
        # Likely diagnostic combo containing both headers
        idx = data.find(b'\x82\x00\xff\x01')
        if idx != -1:
            return "DIAG", data[idx:]
    return "UNKNOWN", data


if __name__ == "__main__":
    radio = VRCM(port="COM9")
    
    try:
        # root = tk.Tk()
        # VRCMControllerGUI(root,radio)
        # root.mainloop()
        # radio.send_command('enter_command_mode')
        # time.sleep(0.1)

        # radio.send_command('status_request')
        # radio.send_command('change_channel', CHANNEL=16)
        # #radio.send_command('broadcast_packets', PACKET_TYPE=0x01)

        # radio.send_command('exit_command_mode')
        # time.sleep(0.2)  # give the radio time to switch from command mode to normal mode

        # ON/OFF payload
        # hdr = THeader(respClient=1, activeClient=1, ptype=PACKET_TYPES["CLIENT_TURNONFF"], state=8, cycle=0)
        # ofp = TOnOffSerialPayload(hdr=hdr, serial=1201)
        # success = radio.radio_loop_timed_multi_command(ofp, time_ms=1800,retries=4)
        # print("ON/OFF Result:", success)
        # radio.discover_robots()
        # check_arrows()
        # # radio.ping('A',1,5)
        # radio.ping('C',3,10)
        # radio.listen()
        #radio.power_bot(1201,True, 'a', 1)
        #radio.add_bot(1201,1,1)
        #radio.power('on')
        radio.add_bot(1202,3,3)
        radio.power('on')
        #radio.set_rf('a')
        #radio.power('on')
        #radio.set_rf('a')
        # radio.toggle_tower('down')
        # time.sleep(2)
        # radio.toggle_tower('up')
        for i in range(10):
            
            print('Try',i)
            
            data = BuildAndSendRcPacket(radio=radio,destCli=1,respCli=1,cycle=6,joystick=EMPTY_JOYSTICK,packettype='OTHER_COMMAND',wait=0.5)
            pkt_type, pkt = identify_packet(data)

            if pkt_type == "STATUS":
                status = ResponsePayload_Status.unpack(pkt[11:])  # skip TRadioPacket header
                print(f"[STATUS] {status}")
                print(status.serial)

            elif pkt_type == "DIAG":
                diag = ResponsePayload_Diag.unpack(pkt[11:])
                print(f"[DIAG] {diag}")

            else:
                print("Unknown packet:", data.hex())
        
    

    finally:
        radio.close()

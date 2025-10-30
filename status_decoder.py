import struct
from dataclasses import dataclass
from typing import Tuple, Optional

@dataclass
class ResponsePayload_Status:
    """
    Status packet from robot matching C struct ResponsePayload_Status
    """
    # Header fields
    packetType: int      # uint8_t
    clientId: int        # uint8_t
    state: int           # uint8_t
    errors: int          # uint8_t
    
    # GPS/Position data
    utmX: int            # int32_t (multiply by 0.1 to get actual value)
    utmY: int            # int32_t (multiply by 0.1 to get actual value)
    speed: int           # int8_t (multiply by 0.1 to get m/s)
    motspeed: int        # int8_t (multiply by 0.1 to get motor speed)
    
    # GPS quality info
    gpsInfo: int         # uint8_t (high nibble = num satellites, low nibble = fix type)
    gpsInfo2: int        # uint8_t (GPS2 info, same format)
    
    # Navigation
    COG: int             # int16_t (Course Over Ground, likely in degrees or decidegrees)
    flags: int           # uint8_t
    serial: int          # uint16_t
    
    # Hit detection (size unknown - assuming uint8_t)
    hit_zone: int        # uint8_t
    
    # UTM Zone (appears to be char array, size unknown - assuming 4 bytes based on common UTM zone format)
    utmZone: bytes       # char[4]
    
    # Motor RPMs
    rpm: Tuple[int, int, int, int]  # int16_t[4]

    @classmethod
    def unpack(cls, data: bytes):
        """
        Unpack status packet from bytes.
        Format string breakdown:
        B B B B = 4 header bytes (packetType, clientId, state, errors)
        i i     = 2 int32 (utmX, utmY)
        b b     = 2 int8 (speed, motspeed)
        B B     = 2 uint8 (gpsInfo, gpsInfo2)
        h       = 1 int16 (COG)
        B       = 1 uint8 (flags)
        H       = 1 uint16 (serial)
        B       = 1 uint8 (hit_zone)
        4s      = 4 char (utmZone)
        h h h h = 4 int16 (rpm array)
        """
        # Adjust format string based on actual struct - may need padding
        fmt = "<BBBBiiBBBBhBH B 4s hhhh"
        size = struct.calcsize(fmt)
        
        if len(data) < size:
            raise ValueError(f"Insufficient data: expected at least {size} bytes, got {len(data)}")
        
        fields = struct.unpack(fmt, data[:size])
        
        return cls(
            packetType=fields[0],
            clientId=fields[1],
            state=fields[2],
            errors=fields[3],
            utmX=fields[4],
            utmY=fields[5],
            speed=fields[6],
            motspeed=fields[7],
            gpsInfo=fields[8],
            gpsInfo2=fields[9],
            COG=fields[10],
            flags=fields[11],
            serial=fields[12],
            hit_zone=fields[13],
            utmZone=fields[14],
            rpm=(fields[15], fields[16], fields[17], fields[18])
        )
    
    def get_utm_position(self) -> Tuple[float, float]:
        """Get actual UTM position in meters"""
        return (self.utmX / 10.0, self.utmY / 10.0)
    
    def get_speed_ms(self) -> float:
        """Get speed in m/s"""
        return self.speed / 10.0
    
    def get_motor_speed_ms(self) -> float:
        """Get motor speed in m/s"""
        return self.motspeed / 10.0
    
    def get_gps1_info(self) -> Tuple[int, int]:
        """Extract GPS1 number of satellites and fix type"""
        num_sats = (self.gpsInfo >> 4) & 0x0F
        fix_type = self.gpsInfo & 0x0F
        return (num_sats, fix_type)
    
    def get_gps2_info(self) -> Tuple[int, int]:
        """Extract GPS2 number of satellites and fix type"""
        num_sats = (self.gpsInfo2 >> 4) & 0x0F
        fix_type = self.gpsInfo2 & 0x0F
        return (num_sats, fix_type)


@dataclass
class ResponsePayload_Diag:
    """
    Diagnostics packet from robot matching C struct ResponsePayload_Diag
    """
    # Header fields
    packetType: int      # uint8_t
    clientId: int        # uint8_t
    state: int           # uint8_t
    errors: int          # uint8_t
    
    # Battery data (3 batteries)
    vbat: Tuple[int, int, int]        # uint16_t[3] - voltage (add 40000, multiply by 100 to get mV)
    ibat: Tuple[int, int, int]        # int16_t[3] - current (multiply by 100 to get mA)
    bcap: Tuple[int, int, int]        # uint8_t[3] - battery capacity (state of charge %)
    btemp1: Tuple[int, int, int]      # int8_t[3] - battery temp sensor 1
    btemp2: Tuple[int, int, int]      # int8_t[3] - battery temp sensor 2
    btemp3: Tuple[int, int, int]      # int8_t[3] - battery temp sensor 3
    
    # Other temperatures
    otemp: Tuple[int, int, int, int, int]  # int8_t[5] - other temperature sensors
    
    # Fan speeds
    fans: Tuple[int, int, int, int, int]   # uint8_t[5] - fan speeds
    
    # Serial number
    serial: int          # uint16_t

    @classmethod
    def unpack(cls, data: bytes):
        """
        Unpack diagnostics packet from bytes.
        Format string breakdown:
        B B B B     = 4 header bytes
        H H H       = 3 uint16 (vbat array)
        h h h       = 3 int16 (ibat array)
        B B B       = 3 uint8 (bcap array)
        b b b       = 3 int8 (btemp1 array)
        b b b       = 3 int8 (btemp2 array)
        b b b       = 3 int8 (btemp3 array)
        b b b b b   = 5 int8 (otemp array)
        B B B B B   = 5 uint8 (fans array)
        H           = 1 uint16 (serial)
        """
        fmt = "<BBBB HHH hhh BBB bbb bbb bbb bbbbb BBBBB H"
        size = struct.calcsize(fmt)
        
        if len(data) < size:
            raise ValueError(f"Insufficient data: expected at least {size} bytes, got {len(data)}")
        
        fields = struct.unpack(fmt, data[:size])
        
        return cls(
            packetType=fields[0],
            clientId=fields[1],
            state=fields[2],
            errors=fields[3],
            vbat=(fields[4], fields[5], fields[6]),
            ibat=(fields[7], fields[8], fields[9]),
            bcap=(fields[10], fields[11], fields[12]),
            btemp1=(fields[13], fields[14], fields[15]),
            btemp2=(fields[16], fields[17], fields[18]),
            btemp3=(fields[19], fields[20], fields[21]),
            otemp=(fields[22], fields[23], fields[24], fields[25], fields[26]),
            fans=(fields[27], fields[28], fields[29], fields[30], fields[31]),
            serial=fields[32]
        )
    
    def get_battery_voltage(self, battery_index: int) -> float:
        """Get battery voltage in mV (0 = no battery)"""
        if battery_index < 0 or battery_index > 2:
            raise ValueError("Battery index must be 0, 1, or 2")
        
        raw = self.vbat[battery_index]
        if raw == 0:
            return 0.0
        return (raw * 100 + 40000)  # Reverse the encoding: (v - 40000) / 100
    
    def get_battery_current(self, battery_index: int) -> float:
        """Get battery current in mA"""
        if battery_index < 0 or battery_index > 2:
            raise ValueError("Battery index must be 0, 1, or 2")
        
        return self.ibat[battery_index] * 100


@dataclass
class RadioPacket:
    """
    Radio packet wrapper - this is what comes from the radio module.
    The robot response is inside the payload.
    """
    cmd: int           # 0x81 = response from robot, 0x82 = SDC from radio
    paylen: int
    reserved: int
    retries: int
    dest1: int
    dest2: int
    dest3: int
    payload: bytes
    
    @classmethod
    def unpack(cls, data: bytes):
        """Unpack radio packet header and payload"""
        if len(data) < 7:
            raise ValueError(f"Radio packet too short: {len(data)} bytes")
        
        fields = struct.unpack("<BBBBBBB", data[:7])
        payload = data[7:]  # Everything after header is payload
        
        return cls(
            cmd=fields[0],
            paylen=fields[1],
            reserved=fields[2],
            retries=fields[3],
            dest1=fields[4],
            dest2=fields[5],
            dest3=fields[6],
            payload=payload
        )


# Packet type constants
RESPONSE_PACK_STATUS = 16
RESPONSE_PACK_DIAG = 17

# Radio command constants
RADIO_CMD_RESPONSE = 0x81  # Response from robot
RADIO_CMD_SDC = 0x82       # Status/Data/Control from radio module


def decode_robot_response(payload: bytes) -> Optional[object]:
    """
    Decode a robot response packet from the payload.
    
    Args:
        payload: Payload bytes (after radio packet header)
    
    Returns:
        ResponsePayload_Status or ResponsePayload_Diag object, or None if not a robot packet
    """
    if len(payload) < 1:
        return None
    
    packet_type = payload[0]
    
    if packet_type == RESPONSE_PACK_STATUS:
        return ResponsePayload_Status.unpack(payload)
    elif packet_type == RESPONSE_PACK_DIAG:
        return ResponsePayload_Diag.unpack(payload)
    else:
        return None


def decode_radio_packet(data: bytes):
    """
    Decode a complete packet from the radio module.
    
    Args:
        data: Raw bytes from radio
    
    Returns:
        tuple: (radio_packet, robot_data)
        - radio_packet: RadioPacket object
        - robot_data: ResponsePayload_Status/Diag or None
    """
    if not data or len(data) < 7:
        return None, None
    
    # Parse radio packet
    radio_packet = RadioPacket.unpack(data)
    
    # Check if this is a robot response (0x81) or radio SDC (0x82)
    if radio_packet.cmd == RADIO_CMD_RESPONSE:
        # This is a response from the robot - decode the payload
        robot_data = decode_robot_response(radio_packet.payload)
        return radio_packet, robot_data
    elif radio_packet.cmd == RADIO_CMD_SDC:
        # This is an SDC packet from the radio module
        # SDC packets may contain an embedded 0x81 robot response packet
        print(f"SDC packet received (radio acknowledgment)")
        
        # Check if there's an embedded 0x81 packet in the payload
        # Look for 0x81 byte in the first few bytes
        if len(radio_packet.payload) > 7:
            # Check if byte at index 0 or nearby is 0x81
            for offset in range(min(4, len(radio_packet.payload) - 7)):
                if radio_packet.payload[offset] == 0x81:
                    print(f"  Found embedded 0x81 packet at offset {offset}")
                    # Try to parse embedded packet starting at this offset
                    embedded_data = radio_packet.payload[offset:]
                    try:
                        embedded_packet = RadioPacket.unpack(embedded_data)
                        if embedded_packet.cmd == 0x81:
                            robot_data = decode_robot_response(embedded_packet.payload)
                            return embedded_packet, robot_data
                    except:
                        pass
        
        return radio_packet, None
    else:
        print(f"Unknown radio command: 0x{radio_packet.cmd:02X}")
        return radio_packet, None


# Example usage
if __name__ == "__main__":
    # Your actual packet data
    test_packet = b'\x82\x00\xff\x01\x81,#Q\xc3U\\\x10!\xc1x\xb1\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x02\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00'
    
    print("Decoding packet...")
    print(f"Raw data ({len(test_packet)} bytes): {test_packet.hex()}")
    print()
    
    # Try different interpretations
    print("=== Interpretation 1: Standard Radio Packet ===")
    radio_packet, robot_data = decode_radio_packet(test_packet)
    
    if radio_packet:
        print(f"Radio Packet:")
        print(f"  Command: 0x{radio_packet.cmd:02X} ({'ROBOT RESPONSE' if radio_packet.cmd == 0x81 else 'SDC/ACK' if radio_packet.cmd == 0x82 else 'UNKNOWN'})")
        print(f"  Payload Length: {radio_packet.paylen}")
        print(f"  Retries: {radio_packet.retries}")
        print(f"  Destination: {radio_packet.dest1:02X} {radio_packet.dest2:02X} {radio_packet.dest3:02X}")
        print(f"  Payload ({len(radio_packet.payload)} bytes): {radio_packet.payload.hex()}")
        print()
    
    if robot_data:
        if isinstance(robot_data, ResponsePayload_Status):
            print("✓ Robot Status Data FOUND:")
            print(f"  Packet Type: {robot_data.packetType}")
            print(f"  Client ID: {robot_data.clientId}")
            print(f"  State: {robot_data.state}")
            print(f"  Errors: 0x{robot_data.errors:02X}")
            print(f"  UTM Position: {robot_data.get_utm_position()}")
            print(f"  Speed: {robot_data.get_speed_ms():.1f} m/s")
            print(f"  Motor Speed: {robot_data.get_motor_speed_ms():.1f} m/s")
            print(f"  GPS1: {robot_data.get_gps1_info()} (sats, fix)")
            print(f"  GPS2: {robot_data.get_gps2_info()} (sats, fix)")
            print(f"  COG: {robot_data.COG}")
            print(f"  Serial: {robot_data.serial}")
            print(f"  RPM: {robot_data.rpm}")
        elif isinstance(robot_data, ResponsePayload_Diag):
            print("✓ Robot Diagnostics Data FOUND:")
            print(f"  Packet Type: {robot_data.packetType}")
            print(f"  Client ID: {robot_data.clientId}")
            print(f"  State: {robot_data.state}")
            print(f"  Errors: 0x{robot_data.errors:02X}")
            for i in range(3):
                print(f"  Battery {i+1}:")
                print(f"    Voltage: {robot_data.get_battery_voltage(i):.0f} mV")
                print(f"    Current: {robot_data.get_battery_current(i):.0f} mA")
                print(f"    Capacity: {robot_data.bcap[i]}%")
                print(f"    Temps: {robot_data.btemp1[i]}°C, {robot_data.btemp2[i]}°C, {robot_data.btemp3[i]}°C")
            print(f"  Other Temps: {robot_data.otemp}")
            print(f"  Fan Speeds: {robot_data.fans}")
    else:
        print("✗ No robot data decoded yet")
        print()
        
        # Try manual parsing - look for packet type 0x10 (16 = RESPONSE_PACK_STATUS)
        print("=== Interpretation 2: Manual Search for Packet Type ===")
        for i in range(len(test_packet) - 4):
            if test_packet[i] == 0x10:  # RESPONSE_PACK_STATUS
                print(f"Found potential status packet at byte {i}")
                try:
                    status = ResponsePayload_Status.unpack(test_packet[i:])
                    print(f"✓ Successfully decoded status packet!")
                    print(f"  Client ID: {status.clientId}")
                    print(f"  State: {status.state}")
                    print(f"  UTM Position: {status.get_utm_position()}")
                    print(f"  Serial: {status.serial}")
                    break
                except Exception as e:
                    print(f"  Failed to decode: {e}")
            elif test_packet[i] == 0x11:  # RESPONSE_PACK_DIAG
                print(f"Found potential diag packet at byte {i}")
                try:
                    diag = ResponsePayload_Diag.unpack(test_packet[i:])
                    print(f"✓ Successfully decoded diag packet!")
                    print(f"  Client ID: {diag.clientId}")
                    print(f"  State: {diag.state}")
                    break
                except Exception as e:
                    print(f"  Failed to decode: {e}")
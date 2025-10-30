import struct
from dataclasses import dataclass
from typing import List, Tuple
import time

# Constants
MAX_PTS_IN_PATH = 200
BYTES_PER_DOWNLOAD_PACKET = 54

@dataclass
class PathPoint:
    """Single waypoint in a path"""
    x: float
    y: float
    flag: int  # int8_t
    
    def pack(self) -> bytes:
        """Pack point into bytes for transmission"""
        return struct.pack("<ffb", self.x, self.y, self.flag)
    
    @classmethod
    def unpack(cls, data: bytes):
        """Unpack point from bytes"""
        x, y, flag = struct.unpack("<ffb", data[:9])
        return cls(x, y, flag)


@dataclass
class TPathForXmit:
    """Path/Scenario structure for transmission to robot"""
    name: str  # 12 chars max
    pathdate: int  # uint32_t (YYMMDD format)
    pathtime: int  # uint32_t (HHMMSS format)
    lat0: float  # long double -> float in Python
    lon0: float  # long double -> float in Python
    x0: float 
    y0: float
    npts: int  # uint16_t - number of points
    curpt: int  # uint16_t - current point index
    pts: List[PathPoint]  # List of path points
    
    def pack(self) -> bytes:
        """Pack entire path structure into bytes for transmission"""
        # Ensure name is exactly 12 bytes
        name_bytes = self.name.encode('ascii')[:12].ljust(12, b'\x00')
        
        # Pack header (everything before pts array)
        # Format: 12s (name) + 2I (pathdate, pathtime) + 4f (lat0, lon0, x0, y0) + 2H (npts, curpt)
        header = struct.pack(
            "<12s2I4f2H",
            name_bytes,
            self.pathdate,
            self.pathtime,
            self.lat0,
            self.lon0,
            self.x0,
            self.y0,
            self.npts,
            self.curpt
        )
        
        # Pack all points
        points_data = b''.join(pt.pack() for pt in self.pts[:self.npts])
        
        return header + points_data
    
    def calculate_checksum(self) -> int:
        """Calculate XOR checksum of packed data"""
        data = self.pack()
        csum = 0
        for byte in data:
            csum ^= byte
        return csum & 0xFFFF
    
    @classmethod
    def from_waypoints(cls, name: str, waypoints: List[Tuple[float, float, int]] = None,
                       lat0: float = 0.0, lon0: float = 0.0,
                       x0: float = 0.0, y0: float = 0.0,
                       pathdate: int = 0, pathtime: int = 0):
        """
        Create path from list of waypoints
        
        Args:
            name: Path name (max 12 chars)
            waypoints: List of (x, y, flag) tuples
            lat0, lon0: Origin latitude/longitude
            x0, y0: UTM origin coordinates
            pathdate: Date in YYMMDD format (e.g., 241025 for Oct 25, 2024)
            pathtime: Time in HHMMSS format (e.g., 143000 for 2:30:00 PM)
        """
        if waypoints is None:
            waypoints = []
        
        pts = [PathPoint(x, y, flag) for x, y, flag in waypoints]
        
        return cls(
            name=name[:12],
            pathdate=pathdate,
            pathtime=pathtime,
            lat0=lat0,
            lon0=lon0,
            x0=x0,
            y0=y0,
            npts=len(pts),
            curpt=0,
            pts=pts
        )


@dataclass
class TRespHeader:
    """Response header (4 bytes)"""
    packetType: int  # uint8_t
    clientId: int  # uint8_t (4 bits)
    state: int  # uint8_t (4 bits)
    errors: int  # uint16_t
    
    def pack(self) -> bytes:
        # Pack clientId and state into one byte
        client_state = ((self.state & 0x0F) << 4) | (self.clientId & 0x0F)
        return struct.pack("<BBH", self.packetType, client_state, self.errors)


@dataclass
class DownloadPayload:
    """Payload for downloading scenario packets"""
    hdr: 'THeader'  # 4 bytes
    totPackets: int  # uint8_t
    packetIdx: int  # uint8_t (1-indexed)
    numBytes: int  # uint8_t
    data: bytes  # BYTES_PER_DOWNLOAD_PACKET bytes
    
    def pack(self) -> bytes:
        """Pack download payload"""
        data_fixed = self.data[:BYTES_PER_DOWNLOAD_PACKET].ljust(BYTES_PER_DOWNLOAD_PACKET, b'\x00')
        return (
            self.hdr.pack() +
            struct.pack("<BBB", self.totPackets, self.packetIdx, self.numBytes) +
            data_fixed
        )
    
    @classmethod
    def unpack(cls, data: bytes, THeader):
        """Unpack download payload"""
        hdr = THeader.unpack(data[:4])
        totPackets, packetIdx, numBytes = struct.unpack("<BBB", data[4:7])
        payload_data = data[7:7+BYTES_PER_DOWNLOAD_PACKET]
        return cls(hdr, totPackets, packetIdx, numBytes, payload_data)


@dataclass
class ResponsePayload_Simple:
    """Simple response payload for download completion"""
    hdr: TRespHeader
    status: int  # uint8_t
    crc: int  # uint16_t
    
    def pack(self) -> bytes:
        return self.hdr.pack() + struct.pack("<BH", self.status, self.crc)


def split_path_into_packets(path: TPathForXmit) -> List[bytes]:
    """Split a path into packets of BYTES_PER_DOWNLOAD_PACKET size"""
    full_data = path.pack()
    packets = []
    
    offset = 0
    while offset < len(full_data):
        chunk = full_data[offset:offset + BYTES_PER_DOWNLOAD_PACKET]
        packets.append(chunk)
        offset += BYTES_PER_DOWNLOAD_PACKET
    
    return packets


def create_download_packet(radio_packet_class, THeader, PACKET_TYPES,
                           packet_data: bytes, packet_idx: int, 
                           total_packets: int, client_id: int,
                           dest1: int = 0xFF, dest2: int = 0xFF, dest3: int = 0xFF,
                           retries: int = 8) -> 'TRadioPacket':
    """Create a single download packet ready to transmit"""
    # Create header
    hdr = THeader(
        respClient=client_id,
        activeClient=client_id,
        ptype=PACKET_TYPES["SCENARIO_DNLOAD"],
        state=0,
        cycle=65518
    )
    
    # Create download payload
    dl_payload = DownloadPayload(
        hdr=hdr,
        totPackets=total_packets,
        packetIdx=packet_idx,
        numBytes=len(packet_data),
        data=packet_data
    )
    
    payload_bytes = dl_payload.pack()
    
    # Create radio packet with high retries
    packet = radio_packet_class(
        cmd=0x81,
        paylen=len(payload_bytes),
        reserved=0,
        retries=retries,
        dest1=dest1,
        dest2=dest2,
        dest3=dest3,
        payload=payload_bytes
    )
    
    return packet


def wait_for_packet_request(radio, timeout: float = 5.0) -> int:
    """
    Wait for robot to request a packet
    Returns: packet index requested (1-based), or 0 if timeout/error
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        # Clear any buffered data first
        radio.ser.reset_input_buffer()
        time.sleep(0.05)
        
        data = radio.read_packet(timeout=0.5)
        print('DATA:',data)
        if data and len(data) >= 7:
            # Check if this is a request packet (cmd=0x81)
            if data[0] == 0x81:
                # Parse the payload to get packet index
                try:
                    # Skip radio header (7 bytes), get download payload
                    if len(data) > 11:
                        # totPackets, packetIdx, numBytes at offset 11, 12, 13
                        packet_idx = data[12]
                        return packet_idx
                except:
                    pass
    
    return 0


def send_scenario_to_robot(radio, path: TPathForXmit, client_id: int, 
                          THeader, TRadioPacket, PACKET_TYPES, TRespHeader,
                          timeout: float = 10.0):
    """
    Send a complete scenario/path to the robot using the proper protocol
    
    The robot REQUESTS each packet, we don't just blast them.
    """
    # Calculate checksum
    checksum = path.calculate_checksum()
    print(f"\n===> Scenario Download Starts: '{path.name}'")
    print(f"     {path.npts} waypoints, checksum=0x{checksum:04X}")
    
    # Split into packets
    packet_data_list = split_path_into_packets(path)
    total_packets = len(packet_data_list)
    
    # Prepend checksum to first packet's data
    csum_bytes = struct.pack("<H", checksum)
    packet_data_list[0] = csum_bytes + packet_data_list[0][2:]
    
    print(f"     Split into {total_packets} packets of {BYTES_PER_DOWNLOAD_PACKET} bytes each\n")
    
    # Track which packets we've sent
    packets_sent = [False] * (total_packets + 1)  # 1-indexed
    
    # Send initial packet to start the download
    print("Sending initial packet to start download...")
    initial_packet = create_download_packet(
        TRadioPacket, THeader, PACKET_TYPES,
        packet_data_list[0], 1, total_packets, client_id, retries=8
    )
    
    radio.send_packet(initial_packet)
    time.sleep(0.2)
    
    # Now wait for SDC response (0x82)
    sdc_received = False
    for _ in range(10):
        resp = radio.read_packet(timeout=0.5)
        if resp and len(resp) > 0 and resp[0] == 0x82:
            print(resp)
            print("Got SDC confirmation (0x82), download protocol active")
            sdc_received = True
            packets_sent[1] = True
            break
        time.sleep(0.1)
    
    if not sdc_received:
        print("ERROR: Did not receive SDC confirmation")
        return False
    
    # Now enter the request-response loop
    # Robot will request packets, we send them
    num_received = 1  # We already sent packet 1
    
    while num_received < total_packets:
        # The robot should now request the next packet
        print(f"\nWaiting for packet request... ({num_received}/{total_packets} sent)")
        
        # Robot sends requests as 0x81 packets with the download payload
        # The packetIdx field tells us which one it wants
        requested_idx = wait_for_packet_request(radio, timeout=timeout)
        
        if requested_idx == 0:
            print("ERROR: Timeout waiting for packet request")
            # Try sending the next sequential packet anyway
            requested_idx = num_received + 1
            if requested_idx > total_packets:
                print("ERROR: All packets sent, but robot stopped requesting")
                break
        
        print(f"Robot requested packet {requested_idx}/{total_packets}")
        
        # Send the requested packet
        if 1 <= requested_idx <= total_packets:
            packet = create_download_packet(
                TRadioPacket, THeader, PACKET_TYPES,
                packet_data_list[requested_idx - 1],
                requested_idx, total_packets, client_id,
                retries=8
            )
            
            radio.send_packet(packet)
            time.sleep(0.1)
            
            if not packets_sent[requested_idx]:
                packets_sent[requested_idx] = True
                num_received += 1
                print(f"  Sent packet {requested_idx} ({num_received}/{total_packets} complete)")
    
    print(f"\n======> All {total_packets} packets sent")
    
    # Send completion message
    print("\nSending download completion message...")
    entire_packet = TRadioPacket(
        cmd=0x81,
        paylen=0,
        reserved=0,
        retries=8,
        dest1=0xFF,
        dest2=0xFF,
        dest3=0xFF,
        payload=b''
    )
    
    response = ResponsePayload_Simple(
        hdr=TRespHeader(
            packetType=PACKET_TYPES["RESPONSE_PACK_DLREQU"],
            clientId=client_id,
            state=0,
            errors=0
        ),
        status=0xFF,  # End of transmission
        crc=checksum
    )
    
    response_bytes = response.pack()
    entire_packet.paylen = len(response_bytes)
    entire_packet.payload = response_bytes
    
    # Try sending completion with retries
    for attempt in range(10):
        print(f"  Sending closeout message (attempt {attempt + 1}/10)")
        radio.send_packet(entire_packet)
        time.sleep(0.3)
        
        # Wait for final SDC with status=1
        resp = radio.read_packet(timeout=0.5)
        if resp and len(resp) >= 4:
            if resp[0] == 0x82 and (len(resp) < 4 or resp[3] == 1):
                print("Protocol termination completed!\n")
                return True
        
    print("WARNING: Did not receive final confirmation, but download may have succeeded\n")
    return True


# Example usage:

from test import Connex4490, THeader, TRadioPacket, PACKET_TYPES

# Create a path
waypoints = [
    (0.0, 0.0, 0),
    (10.0, 0.0, 0),
    (10.0, 10.0, 0),
    (0.0, 10.0, 0),
    (0.0, 0.0, 1),
]

path = TPathForXmit.from_waypoints(
    name="Square",
    waypoints=waypoints,
    pathdate=241009,
    pathtime=120000
)

# Send to robot
radio = Connex4490("COM9")
success = send_scenario_to_robot(
    radio=radio,
    path=path,
    client_id=1,
    THeader=THeader,
    TRadioPacket=TRadioPacket,
    PACKET_TYPES=PACKET_TYPES,
    TRespHeader=TRespHeader
)

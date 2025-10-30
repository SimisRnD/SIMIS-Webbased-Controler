import serial
import struct

# Serial setup
ser = serial.Serial(port="COM9", baudrate=115200, timeout=1)

CLIENT_ID = 0x01  # replace with your actual client ID
g_State = 0x00
g_Errors = 0x00

# Packet constants
CLIENT_TURNONFF = 11
RESPONSE_PACK_ACK = 19

# TRadioPacket minimum size (cmd+paylen+reserved+retries+dest1..3)
HEADER_SIZE = 7

print("ENTERING LOOP")
while True:
    frame = ser.read(87)  # read enough for max payload (80 + 7)
    if not frame or len(frame) < HEADER_SIZE:
        continue

    cmd, paylen, reserved, retries, dest1, dest2, dest3 = frame[:HEADER_SIZE]
    payload = frame[HEADER_SIZE:HEADER_SIZE+paylen]

    # parse THeader from payload (4 bytes)
    if len(payload) < 4:
        continue

    hdr_byte1, hdr_byte2, hdr_byte3, hdr_byte4 = payload[:4]

    respClient = hdr_byte1 & 0x0F
    activeClient = (hdr_byte1 >> 4) & 0x0F
    ptype = hdr_byte2 & 0x0F
    state = (hdr_byte2 >> 4) & 0x0F
    cycle = struct.unpack("<H", payload[2:4])[0]  # little-endian 16-bit

    if activeClient != CLIENT_ID:
        continue  # not for us

    if ptype == CLIENT_TURNONFF:
        # build ResponsePayload_Simple: hdr + status
        # TRespHeader: packetType (1), clientId (1), state (1), errors (1)
        resp_hdr = struct.pack("<BBBB", RESPONSE_PACK_ACK, CLIENT_ID, g_State, g_Errors)
        status = struct.pack("B", 1)
        crc = struct.pack("<H", 0)  # optional CRC if needed
        resp_payload = resp_hdr + status + crc

        # build TRadioPacket
        packet = struct.pack(
            "<BBBB3B", 0x81, len(resp_payload), 0x00, 0x06, dest1, dest2, dest3
        ) + resp_payload


        print(f"Sending reply: {packet.hex()}")
        ser.write(packet)

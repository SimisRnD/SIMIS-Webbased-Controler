import serial

# configure your serial port for the Connex4490
ser = serial.Serial(
    port="COM9",  # change to COMx on Windows
    baudrate=115200,
    timeout=1
)

# payload we are looking for
TARGET_PAYLOAD = bytes([0x11, 0x8B, 0x00, 0x00, 0xB0, 0x04])
RESPONSE_PAYLOAD = bytes([0x19, 0x01, 0X0C, 0x00, 0x00])

print('ENTERING LOOP')
while True:
    # read enough bytes for minimum packet
    frame = ser.read(13)  # your example is 13 bytes total
    if not frame:
        continue

    # sanity check
    if frame[0] != 0x81:
        continue  # not the right API command

    payload_len = frame[1]
    reserved = frame[2]
    rssi = frame[3]
    mac1, mac2, mac3 = frame[4:7]
    payload = frame[7:7+payload_len]

    print(f"Got frame: {frame.hex()}")
    print(f"Payload: {payload.hex()}")

    # check if payload matches the target
    if payload == TARGET_PAYLOAD:
        # build reply
        reply_len = len(RESPONSE_PAYLOAD)
        reply = bytes([
            0x81,                # API command
            reply_len,           # payload length
            0x00,                # reserved
            mac1, mac2, mac3     # echo MACs
        ]) + RESPONSE_PAYLOAD

        print(f"Sending reply: {reply.hex()}")
        ser.write(reply)

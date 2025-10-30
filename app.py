import serial
import time

class Connex4490:
    def __init__(self, port, baudrate=115200, timeout=0.5):
        self.ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        if not self.ser.is_open:
            self.ser.open()
        print(f"Connected to {port} at {baudrate} baud.")

    def send_command(self, command_bytes, wait_response=True):
        """Send a command to the Connex4490 and optionally read response."""
        self.ser.write(bytearray(command_bytes))
        print(f"Sent: {[hex(b) for b in command_bytes]}")
        if wait_response:
            time.sleep(0.05)  # small delay to allow response
            response = self.ser.read_all()
            print(f"Received: {[hex(b) for b in response]}")
            return response
        return None

    # Basic AT/CC commands
    def enter_command_mode(self):
        return self.send_command([0x41,0x54,0x2B,0x2B,0x2B,0x0D])

    def exit_command_mode(self):
        return self.send_command([0xCC,0x41,0x54,0x4F,0x0D])

    def status_request(self):
        return self.send_command([0xCC,0x00,0x00])

    def change_channel(self, new_channel):
        return self.send_command([0xCC,0x02,new_channel])

    def change_server_client(self, mode):
        """mode: 0x00 = Server, 0x03 = Client"""
        return self.send_command([0xCC,0x03,mode])

    def change_sync_channel(self, new_sync_channel):
        return self.send_command([0xCC,0x05,new_sync_channel])

    def sleep_walk_power_down(self):
        return self.send_command([0xCC,0x06])

    def sleep_walk_wake_up(self):
        return self.send_command([0xCC,0x07])

    def broadcast_packet(self, broadcast_type):
        """broadcast_type: 0x00 = Addressed, 0x01 = Broadcast"""
        return self.send_command([0xCC,0x08,broadcast_type])

    def close(self):
        self.ser.close()
        print("Serial connection closed.")
    
    def listen(self):
        return self.ser.read_all()


if __name__ == "__main__":
    # Replace 'COM3' with your serial port (Windows) or '/dev/ttyUSB0' (Linux)

    
    radio = Connex4490(port="COM9")

    try:
        radio.enter_command_mode()
        time.sleep(0.1)

        # Example commands
        radio.status_request()
        radio.change_channel(26)
        # radio.broadcast_packet(0x01)  # send broadcast
        # radio.sleep_walk_power_down()

        radio.exit_command_mode()

        while True:
            time.sleep(0.5)
            reps = radio.listen()
            if reps:
                try:
                    mac1, mac2, mac3 = 0xFF,0xFF,0xFF
                    reply = bytes([0x81,len([0x19, 0x01, 0X0C, 0x00, 0x01]),0]+[mac1,mac2,mac3]+[0x19, 0x01, 0X0C, 0x00, 0x01])
                    print("Recieved:",reps)
                    print('Replying with:',reply)
                    radio.ser.write(reply)
                    time.sleep(0.2)
                    print(radio.listen())
                except ValueError:
                    pass
               
        

    finally:
        
        radio.close()

import serial
import time
from dataclasses import dataclass
import struct


# ----------------------------
# Enhanced Connex4490 class with better debugging
# ----------------------------
class Connex4490Debug:
    def __init__(self, port, baudrate=115200, timeout=0.5):
        self.ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        if not self.ser.is_open:
            self.ser.open()
        print(f"Connected to {port} at {baudrate} baud.")
        
        # Clear any existing data in buffers
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

    def send_command_with_debug(self, cmd_bytes, description=""):
        """Send command with enhanced debugging"""
        print(f"\n--- Sending {description} ---")
        print(f"Command bytes: {[hex(b) for b in cmd_bytes]}")
        print(f"Command as string: {''.join([chr(b) if 32 <= b <= 126 else f'\\x{b:02x}' for b in cmd_bytes])}")
        
        # Clear buffers before sending
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        
        # Send command
        bytes_written = self.ser.write(bytearray(cmd_bytes))
        print(f"Bytes written: {bytes_written}")
        
        # Force flush
        self.ser.flush()
        time.sleep(0.1)  # Give more time for response
        
        # Read response with multiple attempts
        resp = b''
        for attempt in range(3):
            new_data = self.ser.read_all()
            if new_data:
                resp += new_data
                time.sleep(0.05)  # Wait for more data
            else:
                break
                
        print(f"Response length: {len(resp)} bytes")
        if resp:
            print(f"Response bytes: {[hex(b) for b in resp]}")
            print(f"Response as string: {''.join([chr(b) if 32 <= b <= 126 else f'\\x{b:02x}' for b in resp])}")
        else:
            print("No response received!")
        
        return resp

    def comprehensive_radio_test(self):
        """Comprehensive test of radio functionality"""
        print("=== COMPREHENSIVE CONNEX4490 TEST ===\n")
        
        # Test 1: Enter command mode
        print("1. Testing command mode entry...")
        enter_cmd = [0x41, 0x54, 0x2B, 0x2B, 0x2B, 0x0D]  # AT+++\r
        resp = self.send_command_with_debug(enter_cmd, "Enter Command Mode")
        
        if not resp or len(resp) < 4:
            print("❌ FAILED: Could not enter command mode")
            return False
        
        expected = [0xCC, 0x43, 0x4F, 0x4D]  # CCOM
        if list(resp[:4]) == expected:
            print("✅ SUCCESS: Entered command mode")
        else:
            print(f"❌ FAILED: Expected {[hex(b) for b in expected]}, got {[hex(b) for b in resp[:4]]}")
            return False
        
        # Test 2: Get status
        print("\n2. Testing status request...")
        status_cmd = [0xCC, 0x00, 0x00]
        resp = self.send_command_with_debug(status_cmd, "Status Request")
        
        if resp and len(resp) >= 3:
            print(f"✅ Status - Firmware: 0x{resp[1]:02X}, Status: 0x{resp[2]:02X}")
            status_map = {0x00: "Server mode", 0x01: "Client in range", 0x03: "Out of range"}
            print(f"   Status meaning: {status_map.get(resp[2], 'Unknown')}")
        else:
            print("❌ FAILED: No status response")
        
        # Test 3: Check channel
        print("\n3. Testing channel change...")
        channel_cmd = [0xCC, 0x02, 0x0A]  # Channel 10
        resp = self.send_command_with_debug(channel_cmd, "Change Channel to 10")
        
        if resp and len(resp) >= 2 and resp[1] == 0x0A:
            print("✅ SUCCESS: Channel changed to 10")
        else:
            print("❌ FAILED: Channel change failed")
        
        # Test 4: Set broadcast mode
        print("\n4. Testing broadcast mode...")
        broadcast_cmd = [0xCC, 0x08, 0x01]  # Enable broadcast
        resp = self.send_command_with_debug(broadcast_cmd, "Enable Broadcast")
        
        if resp and len(resp) >= 1:
            print("✅ SUCCESS: Broadcast mode configured")
        else:
            print("❌ FAILED: Broadcast configuration failed")
        
        # Test 5: Check transmit buffer
        print("\n5. Testing transmit buffer status...")
        buffer_cmd = [0xCC, 0x30]
        resp = self.send_command_with_debug(buffer_cmd, "Check Transmit Buffer")
        
        if resp and len(resp) >= 2:
            buffer_status = "Empty" if resp[1] == 0x01 else "Has data"
            print(f"✅ Transmit buffer status: {buffer_status}")
        else:
            print("❌ FAILED: Could not check buffer status")
        
        # Test 6: Exit command mode
        print("\n6. Testing command mode exit...")
        exit_cmd = [0xCC, 0x41, 0x54, 0x4F, 0x0D]  # CCATO\r
        resp = self.send_command_with_debug(exit_cmd, "Exit Command Mode")
        resp = self.send_command_with_debug(exit_cmd, "Exit Command Mode")
        
        expected_exit = [0xCC, 0x44, 0x41, 0x54]  # CDAT
        if resp and len(resp) >= 4 and list(resp[:4]) == expected_exit:
            print("✅ SUCCESS: Exited command mode")
            return True
        else:
            print("❌ FAILED: Could not exit command mode")
            return False

    def send_test_packet_with_debug(self):
        """Send a test packet with detailed debugging"""
        print("\n=== PACKET TRANSMISSION TEST ===")
        
        # Create a simple test packet
        test_payload = b"TEST_PACKET_123"
        
        # Build packet header (7 bytes) + payload
        packet_data = bytearray([
            0x81,           # cmd - packet transmission
            len(test_payload),  # paylen
            0x00,           # reserved
            0x0B,           # retries
            0xC5,           # dest1
            0xF6,           # dest2
            0x3C            # dest3
        ])
        
        # Add payload and pad to ensure proper length
        packet_data.extend(test_payload)
        packet_data.extend(b'\x00' * (80 - len(test_payload)))  # Pad to 80 bytes payload
        
        print(f"Packet length: {len(packet_data)} bytes")
        print(f"Header: {[hex(b) for b in packet_data[:7]]}")
        print(f"Payload (first 20 bytes): {[hex(b) for b in packet_data[7:27]]}")
        
        # Send the packet
        print("\nSending packet...")
        bytes_written = self.ser.write(packet_data)
        print(f"Bytes written: {bytes_written}")
        self.ser.flush()
        
        # Wait and check for any response
        time.sleep(0.5)
        resp = self.ser.read_all()
        
        if resp:
            print(f"Response received: {len(resp)} bytes")
            print(f"Response: {[hex(b) for b in resp]}")
        else:
            print("No immediate response (this may be normal for data packets)")
        
        return True

    def check_hardware_pins(self):
        """Check hardware-related settings"""
        print("\n=== HARDWARE PIN CHECK ===")
        
        # Enter command mode first
        enter_cmd = [0x41, 0x54, 0x2B, 0x2B, 0x2B, 0x0D]
        self.send_command_with_debug(enter_cmd, "Enter Command Mode")
        time.sleep(0.1)
        
        # Read digital inputs
        print("\nChecking digital inputs...")
        digital_input_cmd = [0xCC, 0x20]
        resp = self.send_command_with_debug(digital_input_cmd, "Read Digital Inputs")
        
        if resp and len(resp) >= 2:
            print(f"Digital input state: 0x{resp[1]:02X} (binary: {resp[1]:08b})")
        
        # Read supply voltage
        print("\nChecking supply voltage...")
        voltage_cmd = [0xCC, 0xA5]
        resp = self.send_command_with_debug(voltage_cmd, "Read Supply Voltage")
        
        if resp and len(resp) >= 2:
            voltage = resp[1] * 0.1
            print(f"Supply voltage: {voltage:.1f}V")
            if voltage < 3.0:
                print("⚠️  WARNING: Low supply voltage may affect transmission")
        
        # Exit command mode
        exit_cmd = [0xCC, 0x41, 0x54, 0x4F, 0x0D]
        self.send_command_with_debug(exit_cmd, "Exit Command Mode")

    def listening_mode(self, duration_seconds=60):
        """
        Pure listening mode - monitors and displays all incoming data
        """
        print(f"\n=== LISTENING MODE ({duration_seconds} seconds) ===")
        print("Monitoring for incoming packets and data...")
        print("Press Ctrl+C to stop early\n")
        
        # Make sure we're not in command mode
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        
        start_time = time.time()
        packet_count = 0
        
        try:
            while time.time() - start_time < duration_seconds:
                # Check for any incoming data
                if self.ser.in_waiting > 0:
                    # Try to read a full packet (87 bytes for Connex4490)
                    data = self.ser.read(87)
                    
                    if len(data) > 0:
                        packet_count += 1
                        print(f"\n--- PACKET {packet_count} at {time.time() - start_time:.2f}s ---")
                        print(f"Length: {len(data)} bytes")
                        print(f"Raw hex: {' '.join([f'{b:02X}' for b in data])}")
                        
                        # Try to parse as Connex4490 packet if it's 87 bytes
                        if len(data) == 87:
                            self.parse_received_packet(data)
                        elif len(data) >= 7:
                            # Partial packet or different format
                            print(f"Header bytes: {[f'0x{b:02X}' for b in data[:7]]}")
                            if len(data) > 7:
                                print(f"Payload preview: {data[7:min(27, len(data))]}")
                        
                        # Try to interpret as text
                        printable = ''.join([chr(b) if 32 <= b <= 126 else '.' for b in data])
                        if any(32 <= b <= 126 for b in data):
                            print(f"As text: {printable}")
                
                time.sleep(0.01)  # Small delay to prevent excessive CPU usage
                
        except KeyboardInterrupt:
            print(f"\n\nListening stopped by user after {time.time() - start_time:.2f} seconds")
        
        print(f"\nListening complete. Received {packet_count} packets total.")
        return packet_count

    def parse_received_packet(self, data):
        """Parse and display a received 87-byte packet"""
        try:
            # Extract header (first 7 bytes)
            cmd = data[0]
            paylen = data[1] 
            reserved = data[2]
            retries = data[3]
            dest1 = data[4]
            dest2 = data[5]
            dest3 = data[6]
            
            print(f"CMD: 0x{cmd:02X} | PayLen: {paylen} | Reserved: 0x{reserved:02X}")
            print(f"Retries: 0x{retries:02X} | Dest: {dest1:02X}-{dest2:02X}-{dest3:02X}")
            
            # Extract payload (next paylen bytes)
            if paylen > 0 and paylen <= 80:
                payload = data[7:7+paylen]
                print(f"Payload ({paylen} bytes): {' '.join([f'{b:02X}' for b in payload])}")
                
                # Try to parse as your TOnOffSerialPayload structure
                if paylen >= 6:
                    try:
                        # Parse header structure (4 bytes)
                        byte1 = payload[0]
                        byte2 = payload[1] 
                        cycle = int.from_bytes(payload[2:4], byteorder='little')
                        
                        resp_client = byte1 & 0x0F
                        active_client = (byte1 >> 4) & 0x0F
                        ptype = byte2 & 0x0F
                        state = (byte2 >> 4) & 0x0F
                        
                        print(f"  Header: RespClient={resp_client}, ActiveClient={active_client}")
                        print(f"          PType={ptype}, State={state}, Cycle={cycle}")
                        
                        # Parse serial number if present
                        if paylen >= 6:
                            serial = int.from_bytes(payload[4:6], byteorder='little')
                            print(f"  Serial: {serial}")
                            
                    except Exception as e:
                        print(f"  Could not parse payload structure: {e}")
                
                # Show payload as text if printable
                printable_payload = ''.join([chr(b) if 32 <= b <= 126 else '.' for b in payload])
                if any(32 <= b <= 126 for b in payload):
                    print(f"  As text: '{printable_payload}'")
            
            # Command type interpretation
            cmd_types = {
                0x81: "Data packet",
                0x82: "SDC (Sync/Control) packet", 
                0xCC: "Command mode response"
            }
            print(f"Packet type: {cmd_types.get(cmd, 'Unknown')}")
            
        except Exception as e:
            print(f"Error parsing packet: {e}")

    def continuous_listen_with_stats(self, duration_seconds=300):
        """
        Enhanced listening mode with statistics and filtering
        """
        print(f"\n=== ENHANCED LISTENING MODE ({duration_seconds} seconds) ===")
        print("Monitoring with statistics and packet analysis...")
        print("Press Ctrl+C to stop early\n")
        
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        
        start_time = time.time()
        stats = {
            'total_packets': 0,
            'data_packets': 0,
            'sdc_packets': 0,
            'command_responses': 0,
            'unknown_packets': 0,
            'bytes_received': 0
        }
        
        try:
            while time.time() - start_time < duration_seconds:
                if self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting)  # Read all available
                    
                    if len(data) > 0:
                        stats['bytes_received'] += len(data)
                        
                        # Process data in chunks if we got multiple packets
                        offset = 0
                        while offset < len(data):
                            if len(data) - offset >= 87:
                                # Full packet
                                packet = data[offset:offset+87]
                                self.process_packet_for_stats(packet, stats)
                                offset += 87
                            else:
                                # Partial or different sized data
                                remaining = data[offset:]
                                print(f"\nPartial/Other data ({len(remaining)} bytes): {' '.join([f'{b:02X}' for b in remaining])}")
                                break
                
                # Print periodic stats
                if int(time.time() - start_time) % 10 == 0 and stats['total_packets'] > 0:
                    elapsed = time.time() - start_time
                    self.print_stats(stats, elapsed)
                
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print(f"\n\nListening stopped by user")
        
        elapsed = time.time() - start_time
        print(f"\n=== FINAL STATISTICS ===")
        self.print_stats(stats, elapsed)

    def process_packet_for_stats(self, packet_data, stats):
        """Process a packet and update statistics"""
        stats['total_packets'] += 1
        cmd = packet_data[0]
        
        print(f"\n[{stats['total_packets']}] ", end="")
        
        if cmd == 0x81:
            stats['data_packets'] += 1
            print("DATA PACKET")
            self.parse_received_packet(packet_data)
        elif cmd == 0x82:
            stats['sdc_packets'] += 1 
            print("SDC PACKET")
            self.parse_received_packet(packet_data)
        elif cmd == 0xCC:
            stats['command_responses'] += 1
            print("COMMAND RESPONSE")
        else:
            stats['unknown_packets'] += 1
            print(f"UNKNOWN PACKET (CMD: 0x{cmd:02X})")
            
    def print_stats(self, stats, elapsed):
        """Print current statistics"""
        print(f"\n--- Stats after {elapsed:.1f}s ---")
        print(f"Total packets: {stats['total_packets']}")
        print(f"Data packets (0x81): {stats['data_packets']}")
        print(f"SDC packets (0x82): {stats['sdc_packets']}")
        print(f"Command responses (0xCC): {stats['command_responses']}")
        print(f"Unknown packets: {stats['unknown_packets']}")
        print(f"Total bytes: {stats['bytes_received']}")
        if elapsed > 0:
            print(f"Rate: {stats['total_packets']/elapsed:.2f} packets/sec")

    def close(self):
        self.ser.close()
        print("\nSerial connection closed.")


# ----------------------------
# Quick fixes for original code
# ----------------------------
class QuickFix:
    """Quick fixes to apply to your original code"""
    
    @staticmethod
    def fixed_send_packet(radio_instance, packet):
        """Fixed version of send_packet method"""
        # Ensure we're not in command mode
        data = packet.pack()
        
        # Important: Only send header + actual payload length, not full 87 bytes
        actual_length = 7 + packet.paylen
        data_to_send = data[:actual_length]
        
        print(f"--> Sending {len(data_to_send)} bytes, cmd=0x{packet.cmd:02X}, paylen={packet.paylen}")
        print(f"Packet bytes: {[hex(b) for b in data_to_send]}")
        
        # Clear buffers before sending
        radio_instance.ser.reset_input_buffer()
        radio_instance.ser.reset_output_buffer()
        
        # Send the packet
        bytes_written = radio_instance.ser.write(data_to_send)
        radio_instance.ser.flush()  # Force immediate transmission
        
        print(f"Actually wrote {bytes_written} bytes")
        return bytes_written == len(data_to_send)
    
    @staticmethod
    def improved_radio_setup(radio_instance):
        """Improved radio setup sequence"""
        print("=== IMPROVED RADIO SETUP ===")
        
        # 1. Enter command mode with proper timing
        enter_cmd = [0x41, 0x54, 0x2B, 0x2B, 0x2B, 0x0D]
        radio_instance.ser.write(bytearray(enter_cmd))
        time.sleep(0.2)  # Longer wait
        resp = radio_instance.ser.read_all()
        print(f"Enter command mode response: {[hex(b) for b in resp] if resp else 'No response'}")
        
        # 2. Get and display status
        status_cmd = [0xCC, 0x00, 0x00]
        radio_instance.ser.write(bytearray(status_cmd))
        time.sleep(0.1)
        resp = radio_instance.ser.read_all()
        if resp and len(resp) >= 3:
            print(f"Radio status: FW=0x{resp[1]:02X}, Status=0x{resp[2]:02X}")
        
        # 3. Set channel (try a clear channel)
        channel = 15  # Try a different channel
        channel_cmd = [0xCC, 0x02, channel]
        radio_instance.ser.write(bytearray(channel_cmd))
        time.sleep(0.1)
        resp = radio_instance.ser.read_all()
        print(f"Channel {channel} response: {[hex(b) for b in resp] if resp else 'No response'}")
        
        # 4. Enable broadcast mode
        broadcast_cmd = [0xCC, 0x08, 0x01]
        radio_instance.ser.write(bytearray(broadcast_cmd))
        time.sleep(0.1)
        resp = radio_instance.ser.read_all()
        print(f"Broadcast mode response: {[hex(b) for b in resp] if resp else 'No response'}")
        
        # 5. Check transmit buffer status
        buffer_cmd = [0xCC, 0x30]
        radio_instance.ser.write(bytearray(buffer_cmd))
        time.sleep(0.1)
        resp = radio_instance.ser.read_all()
        if resp and len(resp) >= 2:
            status = "Empty" if resp[1] == 0x01 else "Has data"
            print(f"Transmit buffer: {status}")
        
        # 6. Exit command mode
        exit_cmd = [0xCC, 0x41, 0x54, 0x4F, 0x0D]
        radio_instance.ser.write(bytearray(exit_cmd))
        time.sleep(0.2)  # Longer wait for mode switch
        resp = radio_instance.ser.read_all()
        print(f"Exit command mode response: {[hex(b) for b in resp] if resp else 'No response'}")
        
        print("Setup complete - radio should be ready for data transmission")


# ----------------------------
# Main testing function
# ----------------------------
def main():
    # Update COM port as needed
    global radio
    radio = Connex4490Debug(port="COM9")
    
    try:
        print("=== CONNEX4490 OPERATIONS MENU ===")
        print("1. Run comprehensive diagnostic test")
        print("2. Basic listening mode (60 seconds)")
        print("3. Enhanced listening with stats (300 seconds)")
        print("4. Quick listen (10 seconds)")
        print("5. Send test packet then listen")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == "1":
            print("Starting comprehensive Connex4490 debugging...\n")
            
            if radio.comprehensive_radio_test():
                print("\n✅ Basic radio communication is working!")
                radio.check_hardware_pins()
                radio.send_test_packet_with_debug()
                
                print("\n=== KEY ISSUES IN YOUR ORIGINAL CODE ===")
                print("1. 🔧 send_packet() sends full 87 bytes - should only send header + actual payload")
                print("2. 🔧 Missing ser.flush() after write operations")
                print("3. 🔧 Insufficient delays between command mode operations")
                print("4. 🔧 Not checking command responses before proceeding")
                print("5. 🔧 May need different channel or destination address")
                
            else:
                print("\n❌ Basic radio communication failed!")
                print("Check connections and try listening mode to see if radio is receiving anything.")
        
        elif choice == "2":
            print("Starting basic listening mode...")
            radio.listening_mode(60)
            
        elif choice == "3":
            print("Starting enhanced listening mode...")
            radio.continuous_listen_with_stats(300)
            
        elif choice == "4":
            print("Starting quick listen...")
            radio.listening_mode(10)
            
        elif choice == "5":
            print("Sending test packet then listening...")
            # Quick setup and send
            radio.comprehensive_radio_test()
            radio.send_test_packet_with_debug()
            print("\nNow listening for responses...")
            radio.listening_mode(30)
            
        else:
            print("Invalid choice, running diagnostic test...")
            radio.comprehensive_radio_test()
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("Check your COM port and connections!")
    
    finally:
        exit_cmd = [0xCC, 0x41, 0x54, 0x4F, 0x0D]  # CCATO\r
        radio.send_command_with_debug(exit_cmd, "Exit Command Mode")
        radio.close()


# ----------------------------
# Simple listening-only script
# ----------------------------
def simple_listen_only():
    """Simple script that just listens and prints everything"""
    import serial
    import time
    global radio
    
    # Configure your port here
    PORT = "COM9"
    BAUDRATE = 115200
    
    try:
        ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)
        print(f"Listening on {PORT} at {BAUDRATE} baud...")
        print("Press Ctrl+C to stop\n")
        exit_cmd = [0xCC, 0xC0, 0x54, 0x40, 0x01]  # CCATO\r
        radio.send_command_with_debug(exit_cmd, "Exit Command Mode")
        time.sleep(0.25)
       
        packet_count = 0
        start_time = time.time()
        
        while True:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                packet_count += 1
                
                print(f"\n--- Received {len(data)} bytes at {time.time() - start_time:.2f}s ---")
                print(f"Hex: {' '.join([f'{b:02X}' for b in data])}")
                print(f"ASCII: {''.join([chr(b) if 32 <= b <= 126 else '.' for b in data])}")
                
                if len(data) >= 7:
                    print(f"Header: CMD=0x{data[0]:02X}, PayLen={data[1]}, Dest={data[4]:02X}-{data[5]:02X}-{data[6]:02X}")
            
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print(f"\nStopped listening after {packet_count} packets")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'ser' in locals():
            ser.close()


if __name__ == "__main__":
    # Uncomment the next line for simple listening only
    # simple_listen_only()
    
    # Or run the full menu
    main()
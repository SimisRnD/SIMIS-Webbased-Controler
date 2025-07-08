import serial
import time
import struct
from enum import Enum
from typing import Optional, Union, List, Tuple

class CL4790Mode(Enum):
    """RF Delivery modes for CL4790"""
    BROADCAST = "broadcast"
    AUTO_DESTINATION = "auto_destination"
    ADDRESSED = "addressed"

class CL4790NetworkTopology(Enum):
    """Network topology types"""
    POINT_TO_POINT = "p2p"
    POINT_TO_MULTIPOINT = "p2mp"

class CL4790Controller:
    """
    Python controller class for AeroComm CL4790 Industrial 900MHz RF Transceiver
    
    This class provides methods to configure and control the CL4790 radio including:
    - Setting channel frequency (channel number)
    - Setting baud rate
    - Sending message packets
    - Setting network modes and topology
    """
    
    def __init__(self, port: str, baud_rate: int = 57600, timeout: float = 1.0):
        """
        Initialize CL4790 controller
        
        Args:
            port: Serial port (e.g., 'COM1', '/dev/ttyUSB0')
            baud_rate: Serial baud rate (default 57600 - factory default)
            timeout: Serial timeout in seconds
        """
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.serial_conn: Optional[serial.Serial] = None
        self.is_connected = False
        
        # Configuration cache
        self.current_config = {
            'channel_number': None,
            'system_id': None,
            'baud_rate': None,
            'mode': None,
            'mac_address': None,
            'destination_address': None,
            'api_mode': False
        }
    
    def connect(self) -> bool:
        """
        Establish serial connection to CL4790
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout
            )
            self.is_connected = True
            time.sleep(0.1)  # Allow connection to stabilize
            return True
        except Exception as e:
            print(f"Failed to connect to CL4790: {e}")
            return False
    
    def disconnect(self):
        """Close serial connection"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self.is_connected = False
    
    def _send_command(self, command: str, wait_response: bool = True) -> Optional[str]:
        """
        Send AT command to CL4790
        
        Args:
            command: AT command string
            wait_response: Whether to wait for response
            
        Returns:
            Response string or None if no response expected
        """
        if not self.is_connected or not self.serial_conn:
            raise RuntimeError("Not connected to CL4790")
        
        try:
            # Send command
            self.serial_conn.write((command + '\r\n').encode())
            self.serial_conn.flush()
            
            if wait_response:
                # Wait for response
                response = self.serial_conn.readline().decode().strip()
                return response
            return None
            
        except Exception as e:
            print(f"Command failed: {e}")
            return None
    
    def read_configuration(self) -> dict:
        """
        Read current configuration from CL4790
        
        Returns:
            Dictionary containing current configuration
        """
        if not self.is_connected:
            raise RuntimeError("Not connected to CL4790")
        
        # Note: The manual shows GUI-based configuration
        # In practice, you would need to implement the specific AT commands
        # or configuration protocol used by the CL4790
        
        # This is a placeholder implementation
        config = {
            'channel_number': self.current_config.get('channel_number', 16),
            'system_id': self.current_config.get('system_id', 0),
            'baud_rate': self.current_config.get('baud_rate', 57600),
            'mode': self.current_config.get('mode', CL4790Mode.BROADCAST),
            'mac_address': self.current_config.get('mac_address', '00:00:00:00:00:00'),
            'api_mode': self.current_config.get('api_mode', False)
        }
        
        return config
    
    def set_channel_frequency(self, channel_number: int) -> bool:
        """
        Set channel number (frequency)
        
        Args:
            channel_number: Channel number (16-47, determines frequency hop pattern)
            
        Returns:
            bool: True if successful
        """
        if not 16 <= channel_number <= 47:
            raise ValueError("Channel number must be between 16 and 47")
        
        # Implementation would depend on specific AT command protocol
        # This is a placeholder showing the structure
        success = self._configure_parameter('channel_number', channel_number)
        if success:
            self.current_config['channel_number'] = channel_number
        return success
    
    def set_baud_rate(self, baud_rate: int) -> bool:
        """
        Set interface baud rate
        
        Args:
            baud_rate: Baud rate (common values: 9600, 19200, 38400, 57600, 115200)
            
        Returns:
            bool: True if successful
        """
        valid_rates = [9600, 19200, 38400, 57600, 115200]
        if baud_rate not in valid_rates:
            raise ValueError(f"Baud rate must be one of: {valid_rates}")
        
        success = self._configure_parameter('baud_rate', baud_rate)
        if success:
            self.current_config['baud_rate'] = baud_rate
            # Need to reconnect with new baud rate
            self.disconnect()
            self.baud_rate = baud_rate
            self.connect()
        return success
    
    def set_system_id(self, system_id: int) -> bool:
        """
        Set system ID (0-256) for network security
        
        Args:
            system_id: System ID value
            
        Returns:
            bool: True if successful
        """
        if not 0 <= system_id <= 256:
            raise ValueError("System ID must be between 0 and 256")
        
        success = self._configure_parameter('system_id', system_id)
        if success:
            self.current_config['system_id'] = system_id
        return success
    
    def set_mode(self, mode: CL4790Mode, destination_mac: Optional[str] = "00:00:00:00:00:00") -> bool:
        """
        Set RF delivery mode
        
        Args:
            mode: RF delivery mode (broadcast, auto_destination, addressed)
            destination_mac: MAC address for addressed mode (format: "XX:XX:XX:XX:XX:XX")
            
        Returns:
            bool: True if successful
        """
        if mode == CL4790Mode.ADDRESSED and not destination_mac:
            raise ValueError("Destination MAC required for addressed mode")
        
        success = self._configure_parameter('rf_mode', mode.value)
        if success:
            self.current_config['mode'] = mode
            if destination_mac:
                self.current_config['destination_address'] = destination_mac
        return success
    
    def enable_api_mode(self, enable: bool = True) -> bool:
        """
        Enable/disable API mode for packet-level control
        
        Args:
            enable: True to enable API mode, False to disable
            
        Returns:
            bool: True if successful
        """
        success = self._configure_parameter('api_mode', enable)
        if success:
            self.current_config['api_mode'] = enable
        return success
    
    def send_message(self, message: Union[str, bytes], destination_mac: Optional[str] = None) -> bool:
        """
        Send message packet
        
        Args:
            message: Message to send (string or bytes)
            destination_mac: Optional destination MAC (for addressed mode)
            
        Returns:
            bool: True if message sent successfully
        """
        if not self.is_connected:
            raise RuntimeError("Not connected to CL4790")
        
        if isinstance(message, str):
            message = message.encode('utf-8')
        
        if self.current_config.get('api_mode', False):
            return self._send_api_packet(message, destination_mac)
        else:
            return self._send_transparent_message(message)
    
    def _send_api_packet(self, payload: bytes, destination_mac: Optional[str] = None) -> bool:
        """
        Send packet using API mode format
        
        Args:
            payload: Message payload
            destination_mac: Destination MAC address
            
        Returns:
            bool: True if successful
        """
        if len(payload) > 0x80:
            raise ValueError("Payload too large (max 128 bytes)")
        
        # API packet format: 0x81 + Length + Session + Retries + MAC[3] + Payload
        packet = bytearray()
        packet.append(0x81)  # API header
        packet.append(len(payload))  # Payload length
        packet.append(0x00)  # Session count
        packet.append(0x04)  # Retries (default)
        
        # Destination MAC (3 bytes, LSB first)
        if destination_mac:
            mac_bytes = [int(x, 16) for x in destination_mac.split(':')]
            packet.extend(mac_bytes[-3:])  # Last 3 bytes
        else:
            packet.extend([0xFF, 0xFF, 0xFF])  # Broadcast
        
        packet.extend(payload)
        
        try:
            self.serial_conn.write(packet)
            self.serial_conn.flush()
            return True
        except Exception as e:
            print(f"Failed to send API packet: {e}")
            return False
    
    def _send_transparent_message(self, message: bytes) -> bool:
        """
        Send message in transparent mode
        
        Args:
            message: Message bytes
            
        Returns:
            bool: True if successful
        """
        try:
            self.serial_conn.write(message)
            self.serial_conn.flush()
            return True
        except Exception as e:
            print(f"Failed to send transparent message: {e}")
            return False
    
    def receive_message(self, timeout: Optional[float] = None) -> Optional[bytes]:
        """
        Receive message from CL4790
        
        Args:
            timeout: Receive timeout in seconds
            
        Returns:
            Received message bytes or None if timeout
        """
        if not self.is_connected:
            raise RuntimeError("Not connected to CL4790")
        
        original_timeout = self.serial_conn.timeout
        if timeout is not None:
            self.serial_conn.timeout = timeout
        
        try:
            if self.current_config.get('api_mode', False):
                return self._receive_api_packet()
            else:
                return self._receive_transparent_message()
        finally:
            self.serial_conn.timeout = original_timeout
    
    def _receive_api_packet(self) -> Optional[bytes]:
        """Receive API format packet"""
        try:
            # Look for API header 0x81
            header = self.serial_conn.read(1)
            if not header or header[0] != 0x81:
                return None
            
            # Read length
            length_byte = self.serial_conn.read(1)
            if not length_byte:
                return None
            
            length = length_byte[0]
            
            # Read RSSI values and MAC
            metadata = self.serial_conn.read(5)  # RSSI + RSSI* + MAC[3]
            if len(metadata) < 5:
                return None
            
            # Read payload
            payload = self.serial_conn.read(length)
            if len(payload) < length:
                return None
            
            return payload
            
        except Exception as e:
            print(f"Failed to receive API packet: {e}")
            return None
    
    def _receive_transparent_message(self) -> Optional[bytes]:
        """Receive transparent mode message"""
        try:
            # Read available data
            data = self.serial_conn.read(1024)  # Read up to 1KB
            return data if data else None
        except Exception as e:
            print(f"Failed to receive transparent message: {e}")
            return None
    
    def _configure_parameter(self, parameter: str, value) -> bool:
        """
        Configure a parameter on the CL4790
        
        Note: This is a placeholder implementation. The actual implementation
        would depend on the specific configuration protocol used by the CL4790.
        The manual shows GUI-based configuration, so the actual AT commands
        or configuration protocol would need to be determined.
        
        Args:
            parameter: Parameter name
            value: Parameter value
            
        Returns:
            bool: True if successful
        """
        # Placeholder implementation
        print(f"Setting {parameter} to {value}")
        return True
    
    def get_status(self) -> dict:
        """
        Get current status of CL4790
        
        Returns:
            Dictionary with status information
        """
        return {
            'connected': self.is_connected,
            'port': self.port,
            'baud_rate': self.baud_rate,
            'config': self.current_config.copy()
        }
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

    


# Example usage
if __name__ == "__main__":
    # Example of how to use the CL4790Controller
    
    # Initialize controller
    radio = CL4790Controller('COM9', 57600)  # Adjust port as needed
    
    try:
        # Connect to radio
        if radio.connect():
            print("Connected to CL4790")
            
            # Configure radio
            radio.set_channel_frequency(25)  # Set channel 25
            radio.set_system_id(123)         # Set system ID
            radio.set_mode(CL4790Mode.BROADCAST)  # Set broadcast mode
            
            # Send a message
            message = "Hello from CL4790!"
            if radio.send_message(message):
                print(f"Sent message: {message}")
            
            # Enable API mode for advanced packet control
            radio.enable_api_mode(True)
            
            # Send API packet with specific destination
            api_message = b"API packet data"
            radio.send_message(api_message, "12:34:56:78:9A:BC")
            
            # Receive messages
            received = radio.receive_message(timeout=5.0)
            if received:
                print(f"Received: {received}")
            
            # Check status
            status = radio.get_status()
            print(f"Status: {status}")
            
        else:
            print("Failed to connect to CL4790")
            
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        radio.disconnect()
    
    # Alternative usage with context manager
    print("\nUsing context manager:")
    with CL4790Controller('COM9', 57600) as radio:
        radio.set_channel_frequency(30)
        radio.send_message("Context manager message")
#!/usr/bin/env python3
"""
Integrated HTT Radio Controller - Uses CL4790 radio for multi-robot control
Combines the HTT control system with the CL4790 radio implementation
"""

import time
import struct
import threading
import queue
import json
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import tkinter as tk
from tkinter import ttk, messagebox
import logging

# Import the CL4790 radio controller
from radio import CL4790Controller, CL4790Mode

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants from the original HTT code
NUM_CLIENTS = 8
NUM_NETWORKS = 4
COMM_PERF_SIZE = 20

class RadioState(Enum):
    NORMAL = 0
    FORMATION = 1
    UPLOAD = 2
    UPLOAD_INV = 3
    DOWNLOAD = 4
    SINGLE_COMMAND = 5
    TIMED_MULTI_COMMAND = 6
    TWO_INT_COMMAND = 7
    SINGLE_TRANSACTION = 8
    PING_ALL = 9

class ClientState(Enum):
    INVALID = 0
    INIT = 1
    RC = 2
    FORM_L = 3  # Formation Leader
    FORM_F = 4  # Formation Follower

class PacketType(Enum):
    CONTROLLER_INPUT = 1
    OTHER_COMMAND = 2
    RESPONSE_PACK_DIAG = 3
    RESPONSE_PACK_STATUS = 4
    RESPONSE_PACK_PATHNAME = 5

@dataclass
class JoystickData:
    """Joystick input data"""
    x: int = 0
    y: int = 0
    z: int = 0
    btn: int = 0

@dataclass
class ClientData:
    """Client robot data structure"""
    id: int
    state: ClientState = ClientState.RC
    last_state: ClientState = ClientState.RC
    reported_state: ClientState = ClientState.INVALID
    
    # Position data
    utm_x: int = 0
    utm_y: int = 0
    utm_zone: str = ""
    speed: int = 0
    cog: int = 0  # Course over ground
    
    # GPS data
    num_sat1: int = 0
    gps_fix1: int = 0
    num_sat2: int = 0
    gps_fix2: int = 0
    
    # Battery data
    bvolt: List[int] = None
    bcur: List[int] = None
    bcap: List[int] = None
    btemp1: List[int] = None
    btemp2: List[int] = None
    btemp3: List[int] = None
    
    # Other sensor data
    otemp: List[int] = None
    fans: List[int] = None
    rpm: List[int] = None
    
    # Communication stats
    msg_sent: int = 0
    msg_recv: int = 0
    comm_perf: List[bool] = None
    comm_perf_idx: int = 0
    got_packet_flag: bool = False
    
    # Hit detection
    hit_threshold: int = 1
    hit_time_limit: int = 3
    hit_zone_data: int = 0
    
    # Settings
    hd_sensitivity: int = 5
    zones_enable: bool = False
    sonars_enable: bool = True
    distance_thresh: int = 100
    
    # CL4790 specific
    mac_address: str = "00:00:00:00:00:00"
    
    def __post_init__(self):
        if self.bvolt is None:
            self.bvolt = [0, 0]
        if self.bcur is None:
            self.bcur = [0, 0]
        if self.bcap is None:
            self.bcap = [0, 0]
        if self.btemp1 is None:
            self.btemp1 = [0, 0]
        if self.btemp2 is None:
            self.btemp2 = [0, 0]
        if self.btemp3 is None:
            self.btemp3 = [0, 0]
        if self.otemp is None:
            self.otemp = [0] * 5
        if self.fans is None:
            self.fans = [0] * 5
        if self.rpm is None:
            self.rpm = [0] * 4
        if self.comm_perf is None:
            self.comm_perf = [False] * COMM_PERF_SIZE

class HTTRadioController:
    """Main HTT radio controller class using CL4790 radio"""
    
    def __init__(self, serial_port: str = 'COM9', baud_rate: int = 57600, 
                 channel: int = 25, system_id: int = 123):
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.channel = channel
        self.system_id = system_id
        
        # Initialize CL4790 radio controller
        self.radio = CL4790Controller(serial_port, baud_rate)
        self.running = False
        
        # Communication queues
        self.packet_queue = queue.Queue(maxsize=10)
        self.command_queue = queue.Queue(maxsize=5)
        self.response_queue = queue.Queue(maxsize=5)
        
        # State
        self.radio_state = RadioState.NORMAL
        self.menu_mode = False
        self.ready_to_go = False
        self.cycle = 0
        self.active_client = 1
        
        # Client data with MAC addresses
        self.clients = []
        for i in range(NUM_CLIENTS):
            client = ClientData(i+1)
            # Generate MAC addresses for each client (would be configured in real system)
            client.mac_address = f"12:34:56:78:9A:{i+1:02X}"
            self.clients.append(client)
        
        # Joystick simulation
        self.joystick = JoystickData()
        
        # Threading
        self.radio_thread = None
        self.receive_thread = None
        
    def connect(self) -> bool:
        """Connect to the CL4790 radio"""
        try:
            if self.radio.connect():
                logger.info(f"Connected to CL4790 radio on {self.serial_port}")
                
                # Configure radio
                self.radio.set_channel_frequency(self.channel)
                self.radio.set_system_id(self.system_id)
                self.radio.set_mode(CL4790Mode.ADDRESSED)  # Use addressed mode for multi-robot
                self.radio.enable_api_mode(True)  # Enable API mode for packet control
                
                logger.info(f"CL4790 configured: Channel {self.channel}, System ID {self.system_id}")
                return True
            else:
                logger.error("Failed to connect to CL4790 radio")
                return False
        except Exception as e:
            logger.error(f"Error connecting to radio: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the radio"""
        self.running = False
        if self.radio:
            self.radio.disconnect()
            logger.info("Disconnected from CL4790 radio")
    
    def start(self):
        """Start the HTT radio controller"""
        if not self.connect():
            return False
        
        self.running = True
        self.ready_to_go = True
        
        # Start threads
        self.radio_thread = threading.Thread(target=self._radio_task, daemon=True)
        self.receive_thread = threading.Thread(target=self._receive_task, daemon=True)
        
        self.radio_thread.start()
        self.receive_thread.start()
        
        logger.info("HTT Radio controller started")
        return True
    
    def stop(self):
        """Stop the HTT radio controller"""
        self.running = False
        self.disconnect()
        logger.info("HTT Radio controller stopped")
    
    def _receive_task(self):
        """Receive task - continuously listens for incoming packets"""
        while self.running:
            try:
                # Receive packet with timeout
                packet_data = self.radio.receive_message(timeout=0.1)
                if packet_data:
                    self._process_received_packet(packet_data)
            except Exception as e:
                logger.error(f"Receive task error: {e}")
                time.sleep(0.1)
    
    def _process_received_packet(self, packet_data: bytes):
        """Process received packet from CL4790"""
        try:
            if len(packet_data) < 4:
                logger.warning("Received packet too short")
                return
            
            # Parse response header (matching original HTT format)
            client_id, packet_type, state, errors = struct.unpack('<BBBB', packet_data[:4])
            
            if client_id == 0 or client_id > NUM_CLIENTS:
                logger.warning(f"Invalid client ID: {client_id}")
                return
            
            client = self.clients[client_id - 1]
            client.reported_state = ClientState(state)
            client.msg_recv += 1
            client.got_packet_flag = True
            
            logger.debug(f"Response from client {client_id}: type={packet_type}, state={state}")
            
            # Handle specific response types
            if packet_type == PacketType.RESPONSE_PACK_DIAG.value:
                self._handle_diag_response(client, packet_data)
            elif packet_type == PacketType.RESPONSE_PACK_STATUS.value:
                self._handle_status_response(client, packet_data)
            elif packet_type == PacketType.RESPONSE_PACK_PATHNAME.value:
                self._handle_pathname_response(client, packet_data)
                
        except Exception as e:
            logger.error(f"Error processing received packet: {e}")
    
    def _radio_task(self):
        """Main radio task - handles packet transmission scheduling"""
        schedule = [1, 2, 3, 4, 5, 6, 7, 8]  # Client scheduling
        
        while self.running:
            try:
                # Send packets if ready
                if self.ready_to_go and not self.menu_mode:
                    if self.radio_state == RadioState.NORMAL:
                        self._radio_loop_half_duplex(self.cycle, schedule)
                        self.cycle += 1
                    elif self.radio_state == RadioState.FORMATION:
                        self._radio_loop_formation(self.cycle, schedule)
                        self.cycle += 1
                
                time.sleep(0.1)  # 100ms cycle time (adjusted for radio latency)
                
            except Exception as e:
                logger.error(f"Radio task error: {e}")
                time.sleep(0.1)
    
    def _radio_loop_half_duplex(self, cycle: int, schedule: List[int]):
        """Normal half-duplex radio loop"""
        active_client = schedule[cycle % len(schedule)]
        response_client = schedule[(cycle + 1) % len(schedule)]
        
        self._build_and_send_rc_packet(active_client, response_client, cycle)
    
    def _radio_loop_formation(self, cycle: int, schedule: List[int]):
        """Formation mode radio loop"""
        active_client = schedule[cycle % len(schedule)]
        response_client = schedule[(cycle + 1) % len(schedule)]
        
        self._build_and_send_form_packet(active_client, response_client, cycle)
    
    def _build_and_send_rc_packet(self, dest_client: int, resp_client: int, cycle: int):
        """Build and send RC control packet via CL4790"""
        try:
            # Build RC payload (similar to original HTT format)
            payload = bytearray()
            
            # Header (8 bytes)
            payload.extend(struct.pack('<BBHHB', 
                dest_client,        # activeClient
                resp_client,        # respClient
                cycle & 0xFFFF,     # cycle
                PacketType.CONTROLLER_INPUT.value,  # ptype
                self.clients[dest_client-1].state.value  # state
            ))
            
            # Hit detection settings
            payload.extend(struct.pack('<BB',
                self.clients[dest_client-1].hit_threshold,
                self.clients[dest_client-1].hit_time_limit
            ))
            
            # Joystick data
            if self.menu_mode:
                joy_x = joy_y = joy_z = btns = 0
            else:
                joy_x = self.joystick.x
                joy_y = self.joystick.y
                joy_z = self.joystick.z
                btns = self.joystick.btn
            
            payload.extend(struct.pack('<hhhB', joy_x, joy_y, joy_z, btns))
            
            # Send packet to specific client using CL4790
            client_mac = self.clients[dest_client-1].mac_address
            success = self.radio.send_message(bytes(payload), client_mac)
            
            if success:
                # Update client communication stats
                client = self.clients[resp_client-1]
                client.msg_sent += 1
                client.comm_perf[client.comm_perf_idx] = client.got_packet_flag
                client.got_packet_flag = False
                client.comm_perf_idx = (client.comm_perf_idx + 1) % COMM_PERF_SIZE
                
                if client.msg_sent > 9999:
                    client.msg_sent = 0
                    client.msg_recv = 0
                    
                logger.debug(f"Sent RC packet to client {dest_client}")
            else:
                logger.warning(f"Failed to send packet to client {dest_client}")
                
        except Exception as e:
            logger.error(f"Error building/sending RC packet: {e}")
    
    def _build_and_send_form_packet(self, dest_client: int, resp_client: int, cycle: int):
        """Build and send formation control packet"""
        # Similar to RC packet but with formation-specific payload
        # Implementation would depend on formation control requirements
        try:
            payload = bytearray()
            
            # Formation header
            payload.extend(struct.pack('<BBHHBB', 
                dest_client,
                resp_client,
                cycle & 0xFFFF,
                PacketType.OTHER_COMMAND.value,  # Formation command
                self.clients[dest_client-1].state.value
            ))
            
            # Formation-specific data (placeholder)
            payload.extend(struct.pack('<ff', 0.0, 0.0))  # Formation offset x, y
            
            client_mac = self.clients[dest_client-1].mac_address
            success = self.radio.send_message(bytes(payload), client_mac)
            
            if success:
                logger.debug(f"Sent formation packet to client {dest_client}")
                
        except Exception as e:
            logger.error(f"Error building/sending formation packet: {e}")
    
    def _handle_diag_response(self, client: ClientData, payload: bytes):
        """Handle diagnostic response packet"""
        try:
            if len(payload) < 20:  # Minimum expected size
                return
            
            # Parse diagnostic data (example - adjust based on actual format)
            offset = 4  # Skip header
            
            # GPS data
            if len(payload) >= offset + 8:
                client.utm_x, client.utm_y = struct.unpack('<ii', payload[offset:offset+8])
                offset += 8
            
            # Battery data
            if len(payload) >= offset + 4:
                client.bvolt[0], client.bvolt[1] = struct.unpack('<hh', payload[offset:offset+4])
                offset += 4
                
            logger.debug(f"Processed diagnostic data for client {client.id}")
            
        except Exception as e:
            logger.error(f"Error handling diagnostic response: {e}")
    
    def _handle_status_response(self, client: ClientData, payload: bytes):
        """Handle status response packet"""
        try:
            if len(payload) < 12:
                return
            
            offset = 4  # Skip header
            
            # Speed and course
            if len(payload) >= offset + 4:
                client.speed, client.cog = struct.unpack('<hh', payload[offset:offset+4])
                offset += 4
            
            # GPS status
            if len(payload) >= offset + 4:
                client.num_sat1, client.gps_fix1, client.num_sat2, client.gps_fix2 = struct.unpack('<BBBB', payload[offset:offset+4])
                offset += 4
                
            logger.debug(f"Processed status data for client {client.id}")
            
        except Exception as e:
            logger.error(f"Error handling status response: {e}")
    
    def _handle_pathname_response(self, client: ClientData, payload: bytes):
        """Handle pathname response packet"""
        try:
            if len(payload) < 8:
                return
            
            # Extract pathname data (example)
            pathname = payload[4:].decode('utf-8', errors='ignore').strip('\x00')
            logger.debug(f"Pathname from client {client.id}: {pathname}")
            
        except Exception as e:
            logger.error(f"Error handling pathname response: {e}")
    
    def set_joystick(self, x: int, y: int, z: int, btn: int):
        """Set joystick values"""
        self.joystick.x = x
        self.joystick.y = y
        self.joystick.z = z
        self.joystick.btn = btn
    
    def set_client_state(self, client_id: int, state: ClientState):
        """Set client state"""
        if 1 <= client_id <= NUM_CLIENTS:
            self.clients[client_id - 1].state = state
    
    def get_client_data(self, client_id: int) -> Optional[ClientData]:
        """Get client data"""
        if 1 <= client_id <= NUM_CLIENTS:
            return self.clients[client_id - 1]
        return None
    
    def get_comm_performance(self, client_id: int) -> float:
        """Get communication performance percentage"""
        if 1 <= client_id <= NUM_CLIENTS:
            client = self.clients[client_id - 1]
            return sum(client.comm_perf) / COMM_PERF_SIZE * 100
        return 0.0
    
    def set_radio_channel(self, channel: int):
        """Change radio channel"""
        try:
            if self.radio.set_channel_frequency(channel):
                self.channel = channel
                logger.info(f"Changed radio channel to {channel}")
            else:
                logger.error(f"Failed to change radio channel to {channel}")
        except Exception as e:
            logger.error(f"Error changing radio channel: {e}")
    
    def set_client_mac(self, client_id: int, mac_address: str):
        """Set MAC address for a client"""
        if 1 <= client_id <= NUM_CLIENTS:
            self.clients[client_id - 1].mac_address = mac_address
            logger.info(f"Set MAC address for client {client_id}: {mac_address}")
    
    def get_radio_status(self) -> dict:
        """Get current radio status"""
        return {
            'radio_connected': self.radio.is_connected,
            'channel': self.channel,
            'system_id': self.system_id,
            'mode': self.radio_state.name,
            'cycle': self.cycle,
            'active_client': self.active_client
        }

class HTTRadioControllerGUI:
    """GUI for the HTT radio controller with CL4790 integration"""
    
    def __init__(self, controller: HTTRadioController):
        self.controller = controller
        self.root = tk.Tk()
        self.root.title("HTT Radio Controller - CL4790 Integration")
        self.root.geometry("1000x700")
        
        self.setup_gui()
        
    def setup_gui(self):
        """Setup the GUI components"""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Connection frame
        conn_frame = ttk.LabelFrame(main_frame, text="CL4790 Radio Connection")
        conn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(conn_frame, text="Serial Port:").grid(row=0, column=0, padx=5, pady=5)
        self.port_var = tk.StringVar(value="COM9")
        ttk.Entry(conn_frame, textvariable=self.port_var, width=15).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(conn_frame, text="Channel:").grid(row=0, column=2, padx=5, pady=5)
        self.channel_var = tk.IntVar(value=25)
        ttk.Spinbox(conn_frame, from_=16, to=47, textvariable=self.channel_var, width=10).grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(conn_frame, text="System ID:").grid(row=0, column=4, padx=5, pady=5)
        self.system_id_var = tk.IntVar(value=123)
        ttk.Spinbox(conn_frame, from_=0, to=256, textvariable=self.system_id_var, width=10).grid(row=0, column=5, padx=5, pady=5)
        
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=6, padx=5, pady=5)
        
        self.status_label = ttk.Label(conn_frame, text="Disconnected", foreground="red")
        self.status_label.grid(row=0, column=7, padx=5, pady=5)
        
        # Radio settings frame
        radio_frame = ttk.LabelFrame(main_frame, text="Radio Settings")
        radio_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(radio_frame, text="Change Channel", command=self.change_channel).grid(row=0, column=0, padx=5, pady=5)
        
        ttk.Label(radio_frame, text="Mode:").grid(row=0, column=1, padx=5, pady=5)
        self.mode_var = tk.StringVar(value="NORMAL")
        mode_combo = ttk.Combobox(radio_frame, textvariable=self.mode_var, values=["NORMAL", "FORMATION"], width=10)
        mode_combo.grid(row=0, column=2, padx=5, pady=5)
        mode_combo.bind("<<ComboboxSelected>>", self.change_mode)
        
        # Joystick control frame
        joy_frame = ttk.LabelFrame(main_frame, text="Joystick Control")
        joy_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(joy_frame, text="X:").grid(row=0, column=0, padx=5, pady=5)
        self.joy_x_var = tk.IntVar()
        ttk.Scale(joy_frame, from_=-100, to=100, variable=self.joy_x_var, orient=tk.HORIZONTAL, length=200).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(joy_frame, text="Y:").grid(row=1, column=0, padx=5, pady=5)
        self.joy_y_var = tk.IntVar()
        ttk.Scale(joy_frame, from_=-100, to=100, variable=self.joy_y_var, orient=tk.HORIZONTAL, length=200).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(joy_frame, text="Z:").grid(row=2, column=0, padx=5, pady=5)
        self.joy_z_var = tk.IntVar()
        ttk.Scale(joy_frame, from_=-100, to=100, variable=self.joy_z_var, orient=tk.HORIZONTAL, length=200).grid(row=2, column=1, padx=5, pady=5)
        
        self.btn_var = tk.BooleanVar()
        ttk.Checkbutton(joy_frame, text="Button", variable=self.btn_var).grid(row=3, column=0, columnspan=2, padx=5, pady=5)
        
        # Client status frame
        client_frame = ttk.LabelFrame(main_frame, text="Client Status")
        client_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview for client data
        columns = ('ID', 'MAC Address', 'State', 'Reported State', 'Sent', 'Recv', 'Comm %', 'UTM X', 'UTM Y', 'Speed')
        self.client_tree = ttk.Treeview(client_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.client_tree.heading(col, text=col)
            self.client_tree.column(col, width=90)
        
        scrollbar = ttk.Scrollbar(client_frame, orient=tk.VERTICAL, command=self.client_tree.yview)
        self.client_tree.configure(yscrollcommand=scrollbar.set)
        
        self.client_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Start update timer
        self.update_gui()
    
    def toggle_connection(self):
        """Toggle connection to CL4790 radio"""
        if self.controller.running:
            self.controller.stop()
            self.connect_btn.config(text="Connect")
            self.status_label.config(text="Disconnected", foreground="red")
        else:
            self.controller.serial_port = self.port_var.get()
            self.controller.channel = self.channel_var.get()
            self.controller.system_id = self.system_id_var.get()
            
            if self.controller.start():
                self.connect_btn.config(text="Disconnect")
                self.status_label.config(text="Connected", foreground="green")
            else:
                messagebox.showerror("Error", "Failed to connect to CL4790 radio")
    
    def change_channel(self):
        """Change radio channel"""
        if self.controller.running:
            new_channel = self.channel_var.get()
            self.controller.set_radio_channel(new_channel)
    
    def change_mode(self, event=None):
        """Change radio mode"""
        if self.controller.running:
            mode_name = self.mode_var.get()
            if mode_name == "NORMAL":
                self.controller.radio_state = RadioState.NORMAL
            elif mode_name == "FORMATION":
                self.controller.radio_state = RadioState.FORMATION
    
    def update_gui(self):
        """Update GUI with current data"""
        # Update joystick values
        self.controller.set_joystick(
            self.joy_x_var.get(),
            self.joy_y_var.get(),
            self.joy_z_var.get(),
            1 if self.btn_var.get() else 0
        )
        
        # Update client tree
        for item in self.client_tree.get_children():
            self.client_tree.delete(item)
        
        for i, client in enumerate(self.controller.clients):
            comm_perf = self.controller.get_comm_performance(i + 1)
            values = (
                client.id,
                client.mac_address,
                client.state.name,
                client.reported_state.name,
                client.msg_sent,
                client.msg_recv,
                f"{comm_perf:.1f}%",
                client.utm_x,
                client.utm_y,
                client.speed
            )
            self.client_tree.insert('', 'end', values=values)
        
        # Update status
        if self.controller.running:
            radio_status = self.controller.get_radio_status()
            self.status_label.config(text=f"Connected - Ch:{radio_status['channel']} Cycle:{radio_status['cycle']}")
        
        # Schedule next update
        self.root.after(200, self.update_gui)  # Slower update rate for radio
    
    def run(self):
        """Run the GUI"""
        self.root.mainloop()

def main():
    """Main function"""
    # Create controller
    controller = HTTRadioController()
    
    # Create and run GUI
    gui = HTTRadioControllerGUI(controller)
    
    try:
        gui.run()
    finally:
        controller.stop()

if __name__ == "__main__":
    main()
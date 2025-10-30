
import tkinter as tk
from tkinter import ttk, messagebox
import threading

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from test import VRCM
class VRCMControllerGUI:
    def __init__(self, root, vrcm_instance:VRCM):
        self.root = root
        self.vrcm = vrcm_instance
        self.root.title("VRCM Robot Controller")
        self.root.geometry("800x600")
        
        # Variables
        self.drive_x = tk.IntVar(value=0)
        self.drive_y = tk.IntVar(value=0)
        self.drive_z = tk.IntVar(value=0)
        
        # Track if user is actively dragging sliders
        self.is_dragging_x = False
        self.is_dragging_y = False
        self.is_dragging_z = False
        
        self.setup_ui()
        self.update_bot_list()
        
        # Start the drive command loop
        self.drive_loop()
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # === LEFT PANEL: Bot Management ===
        left_frame = ttk.LabelFrame(main_frame, text="Bot Management", padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # Add Bot Section
        ttk.Label(left_frame, text="Serial Number:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.serial_entry = ttk.Entry(left_frame, width=20)
        self.serial_entry.grid(row=0, column=1, pady=2, padx=5)
        
        ttk.Label(left_frame, text="Client ID:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.client_entry = ttk.Entry(left_frame, width=20)
        self.client_entry.grid(row=1, column=1, pady=2, padx=5)
        
        ttk.Label(left_frame, text="Response ID:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.response_entry = ttk.Entry(left_frame, width=20)
        self.response_entry.grid(row=2, column=1, pady=2, padx=5)
        
        ttk.Button(left_frame, text="Add Bot", command=self.add_bot).grid(
            row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(left_frame, text="Discover Robots", command=self.discover_robots).grid(
    row=4, column=0, columnspan=2, pady=5)
        
        # Bot List
        ttk.Label(left_frame, text="Available Bots:").grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(10,2))
        
        self.bot_listbox = tk.Listbox(left_frame, height=8, width=35)
        self.bot_listbox.grid(row=5, column=0, columnspan=2, pady=5)
        self.bot_listbox.bind('<<ListboxSelect>>', self.on_bot_select)
        
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.bot_listbox.yview)
        scrollbar.grid(row=5, column=2, sticky=(tk.N, tk.S))
        self.bot_listbox.config(yscrollcommand=scrollbar.set)
        
        # RF Channel Selection
        ttk.Label(left_frame, text="RF Channel:").grid(row=6, column=0, sticky=tk.W, pady=(10,2))
        self.rf_var = tk.StringVar(value='A')
        rf_frame = ttk.Frame(left_frame)
        rf_frame.grid(row=7, column=0, columnspan=2, pady=5)
        
        for channel in ['A', 'B', 'C']:
            ttk.Radiobutton(rf_frame, text=channel, variable=self.rf_var, 
                           value=channel, command=self.change_rf).pack(side=tk.LEFT, padx=5)
        
        # Power Control
        power_frame = ttk.Frame(left_frame)
        power_frame.grid(row=8, column=0, columnspan=2, pady=10)
        ttk.Button(power_frame, text="Power ON", command=lambda: self.power_bot('on')).pack(side=tk.LEFT, padx=5)
        ttk.Button(power_frame, text="Power OFF", command=lambda: self.power_bot('off')).pack(side=tk.LEFT, padx=5)
        
        # === RIGHT PANEL: Control ===
        right_frame = ttk.LabelFrame(main_frame, text="Robot Control", padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # Drive Controls
        control_frame = ttk.Frame(right_frame)
        control_frame.pack(pady=10)
        
        # X-axis control
        ttk.Label(control_frame, text="X (Left/Right):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.x_scale = ttk.Scale(control_frame, from_=-100, to=100, orient=tk.HORIZONTAL, 
                           variable=self.drive_x, length=300)
        self.x_scale.grid(row=0, column=1, padx=10, pady=5)
        self.x_scale.bind("<ButtonPress-1>", lambda e: self.on_slider_press('x'))
        self.x_scale.bind("<ButtonRelease-1>", lambda e: self.on_slider_release('x'))
        self.x_label = ttk.Label(control_frame, text="0")
        self.x_label.grid(row=0, column=2, pady=5)
        
        # Y-axis control
        ttk.Label(control_frame, text="Y (Forward/Back):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.y_scale = ttk.Scale(control_frame, from_=-100, to=100, orient=tk.HORIZONTAL, 
                           variable=self.drive_y, length=300)
        self.y_scale.grid(row=1, column=1, padx=10, pady=5)
        self.y_scale.bind("<ButtonPress-1>", lambda e: self.on_slider_press('y'))
        self.y_scale.bind("<ButtonRelease-1>", lambda e: self.on_slider_release('y'))
        self.y_label = ttk.Label(control_frame, text="0")
        self.y_label.grid(row=1, column=2, pady=5)
        
        # Z-axis control (rotation)
        ttk.Label(control_frame, text="Z (Rotation):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.z_scale = ttk.Scale(control_frame, from_=-100, to=100, orient=tk.HORIZONTAL, 
                           variable=self.drive_z, length=300)
        self.z_scale.grid(row=2, column=1, padx=10, pady=5)
        self.z_scale.bind("<ButtonPress-1>", lambda e: self.on_slider_press('z'))
        self.z_scale.bind("<ButtonRelease-1>", lambda e: self.on_slider_release('z'))
        self.z_label = ttk.Label(control_frame, text="0")
        self.z_label.grid(row=2, column=2, pady=5)
        
        # Reset button
        ttk.Button(control_frame, text="Reset All", command=self.reset_drive).grid(
            row=3, column=0, columnspan=3, pady=15)
        
        # Tower Controls
        tower_frame = ttk.LabelFrame(right_frame, text="Tower Control", padding="10")
        tower_frame.pack(pady=20, fill=tk.X)
        
        button_frame = ttk.Frame(tower_frame)
        button_frame.pack()
        
        ttk.Button(button_frame, text="Tower UP", command=lambda: self.toggle_tower('up'), 
                  width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Tower HALF", command=lambda: self.toggle_tower('half'), 
                  width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Tower DOWN", command=lambda: self.toggle_tower('down'), 
                  width=15).pack(side=tk.LEFT, padx=5)
        
        # Status Bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def discover_robots(self):
        """Discover all available robots on all RF channels"""
        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title("Robot Discovery")
        popup.geometry("400x300")
        popup.transient(self.root)
        
        ttk.Label(popup, text="Discovering robots...", font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Text widget to show live updates
        text_widget = tk.Text(popup, height=12, width=45, state='disabled')
        text_widget.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(popup, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.config(yscrollcommand=scrollbar.set)
        
        close_btn = ttk.Button(popup, text="Close", command=popup.destroy, state='disabled')
        close_btn.pack(pady=5)
        
        def update_text(message):
            text_widget.config(state='normal')
            text_widget.insert(tk.END, message + '\n')
            text_widget.see(tk.END)
            text_widget.config(state='disabled')
        
        def discover_thread():
            try:
                # Show initial status
                self.root.after(0, lambda: update_text("Starting discovery..."))
                self.root.after(0, lambda: update_text("Scanning all RF channels (A, B, C)"))
                self.root.after(0, lambda: update_text("This will take about 1 minute...\n"))
                
                # Monkey-patch the VRCM method to send updates
                original_add = self.vrcm.add_avalable_bot
                def tracked_add(rf, id):
                    original_add(rf, id)
                    self.root.after(0, lambda: update_text(f"✓ Found: Channel {rf}, Client ID {id}"))
                
                self.vrcm.add_avalable_bot = tracked_add
                
                # Run discovery
                self.vrcm.discover_robots()
                
                # Restore original method
                self.vrcm.add_avalable_bot = original_add
                
                # Show final results
                discovered = self.vrcm.avalible_bots_dic
                self.root.after(0, lambda: update_text("\n--- DISCOVERY COMPLETE ---"))
                self.root.after(0, lambda: update_text(f"Channel A: {discovered['A']}"))
                self.root.after(0, lambda: update_text(f"Channel B: {discovered['B']}"))
                self.root.after(0, lambda: update_text(f"Channel C: {discovered['C']}"))
                
                self.root.after(0, lambda: close_btn.config(state='normal'))
                self.root.after(0, lambda: self.status_var.set("Discovery complete"))
                
            except Exception as e:
                self.root.after(0, lambda: update_text(f"\nERROR: {str(e)}"))
                self.root.after(0, lambda: close_btn.config(state='normal'))
                self.root.after(0, lambda: self.status_var.set("Discovery failed"))
        
        self.status_var.set("Discovering robots...")
        threading.Thread(target=discover_thread, daemon=True).start()

    def update_bot_list(self):
        """Update the bot listbox with current bots"""
        self.bot_listbox.delete(0, tk.END)
        bots = self.vrcm.avalible_bots()
        for i, bot in enumerate(bots):
            display = f"Bot {i}: Serial={bot['serial number']}, Client={bot['client ID']}"
            self.bot_listbox.insert(tk.END, display)
        
        if self.vrcm.current is not None:
            self.bot_listbox.selection_set(self.vrcm.current)
            
    def add_bot(self):
        """Add a new bot"""
        serial = self.serial_entry.get().strip()
        client = self.client_entry.get().strip()
        response = self.response_entry.get().strip()
        
        if not all([serial, client, response]):
            messagebox.showwarning("Input Error", "Please fill all fields")
            return
        
        try:
            success = self.vrcm.add_bot(serial, client, response)
            if success:
                self.status_var.set(f"Bot added successfully: {serial}")
                self.update_bot_list()
                # Clear entries
                self.serial_entry.delete(0, tk.END)
                self.client_entry.delete(0, tk.END)
                self.response_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Connection Error", "Failed to connect to bot")
                self.status_var.set("Failed to add bot")
        except Exception as e:
            messagebox.showerror("Error", f"Error adding bot: {str(e)}")
            self.status_var.set("Error adding bot")
    
    def on_bot_select(self, event):
        """Handle bot selection"""
        selection = self.bot_listbox.curselection()
        if selection:
            index = selection[0]
            self.vrcm.set_current_bot(index)
            self.status_var.set(f"Selected bot {index}")
    
    def change_rf(self):
        """Change RF channel"""
        channel = self.rf_var.get()
        self.vrcm.set_rf(channel)
        self.status_var.set(f"RF channel changed to {channel}")
    
    def power_bot(self, state):
        """Power bot on or off"""
        if self.vrcm.current is None:
            messagebox.showwarning("No Bot Selected", "Please select a bot first")
            return
        
        try:
            result = self.vrcm.power(state)
            if result:
                self.status_var.set(f"Bot powered {state.upper()}")
            else:
                messagebox.showerror("Power Error", f"Failed to power {state} bot")
        except Exception as e:
            messagebox.showerror("Error", f"Error controlling power: {str(e)}")
    
    def drive_loop(self):
        """Continuously send drive commands every 0.5 seconds"""
        if self.vrcm.current is not None:
            
            try:
                x = int(self.drive_x.get())
                y = int(self.drive_y.get())
                z = int(self.drive_z.get())
                print('DRIVING:',self.vrcm.bots[self.vrcm.current]['serial number'],f'x:{x},y:{y},z:{z}' )
                
                # Update labels
                self.x_label.config(text=str(x))
                self.y_label.config(text=str(y))
                self.z_label.config(text=str(z))
                
                if x !=0 or y!=0 or z!=0:
                # Send drive command
                    self.vrcm.drive(x, y, z)
            except Exception as e:
                self.status_var.set(f"Drive error: {str(e)}")
        
        # Schedule next update in 500ms (0.5 seconds)
        self.root.after(500, self.drive_loop)
    
    def on_slider_press(self, axis):
        """Called when user starts dragging a slider"""
        if axis == 'x':
            self.is_dragging_x = True
        elif axis == 'y':
            self.is_dragging_y = True
        elif axis == 'z':
            self.is_dragging_z = True
    
    def on_slider_release(self, axis):
        """Called when user releases a slider - reset to zero"""
        if axis == 'x':
            self.is_dragging_x = False
            self.drive_x.set(0)
        elif axis == 'y':
            self.is_dragging_y = False
            self.drive_y.set(0)
        elif axis == 'z':
            self.is_dragging_z = False
            self.drive_z.set(0)
    
    def reset_drive(self):
        """Reset all drive controls to zero"""
        self.drive_x.set(0)
        self.drive_y.set(0)
        self.drive_z.set(0)
        if self.vrcm.current is not None:
            self.vrcm.drive(0, 0, 0)
        self.status_var.set("Drive controls reset")
    
    def toggle_tower(self, position):
        """Toggle tower position"""
        if self.vrcm.current is None:
            messagebox.showwarning("No Bot Selected", "Please select a bot first")
            return
        
        try:
            self.vrcm.toggle_tower(position)
            self.status_var.set(f"Tower moved to {position.upper()}")
        except Exception as e:
            messagebox.showerror("Error", f"Error controlling tower: {str(e)}")
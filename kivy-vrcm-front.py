"""
VRCM Robot Control - Kivy Android Application
Main application file for tablet control interface
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
import threading
import time

# Import your existing VRCM code
# For Android, you'll need to ensure pyserial and dependencies are included
try:
    from test import VRCM, TJoystick, EMPTY_JOYSTICK, BuildAndSendRcPacket
    from test import ResponsePayload_Status, ResponsePayload_Diag
    from tester import TPathForXmit, send_scenario_to_robot
    from test import THeader, TRadioPacket, PACKET_TYPES, TRespHeader
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import VRCM modules: {e}")
    IMPORTS_AVAILABLE = False


class ConnectionScreen(Screen):
    """Initial connection screen for setting up radio link"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Title
        title = Label(text='VRCM Robot Control', font_size='24sp', size_hint_y=0.2)
        layout.add_widget(title)
        
        # Connection form
        form = GridLayout(cols=2, spacing=10, size_hint_y=0.6)
        
        # Serial port selection (Android uses USB OTG)
        form.add_widget(Label(text='Serial Port:'))
        self.port_input = TextInput(
            text='/dev/ttyUSB0',
            multiline=False,
            hint_text='e.g., /dev/ttyUSB0'
        )
        form.add_widget(self.port_input)
        
        # Baud rate
        form.add_widget(Label(text='Baud Rate:'))
        self.baud_spinner = Spinner(
            text='115200',
            values=('9600', '57600', '115200', '230400')
        )
        form.add_widget(self.baud_spinner)
        
        # RF Channel
        form.add_widget(Label(text='RF Channel:'))
        self.channel_spinner = Spinner(
            text='A',
            values=('A', 'B', 'C')
        )
        form.add_widget(self.channel_spinner)
        
        layout.add_widget(form)
        
        # Status label
        self.status_label = Label(
            text='Not connected',
            color=(1, 1, 0, 1),
            size_hint_y=0.1
        )
        layout.add_widget(self.status_label)
        
        # Connect button
        connect_btn = Button(
            text='Connect to Radio',
            size_hint_y=0.2,
            background_color=(0.2, 0.6, 0.2, 1)
        )
        connect_btn.bind(on_press=self.connect_radio)
        layout.add_widget(connect_btn)
        
        self.add_widget(layout)
    
    def connect_radio(self, instance):
        """Attempt to connect to radio module"""
        if not IMPORTS_AVAILABLE:
            self.show_error("VRCM modules not available")
            return
        
        port = self.port_input.text
        baud = int(self.baud_spinner.text)
        channel = self.channel_spinner.text
        
        try:
            # Create radio instance and store in app
            app = App.get_running_app()
            app.radio = VRCM(port=port, baudrate=baud, timeout=0.5)
            app.radio.set_rf(channel)
            
            self.status_label.text = f'Connected to {port}'
            self.status_label.color = (0, 1, 0, 1)
            
            # Switch to robot management screen
            self.manager.current = 'robot_manager'
            
        except Exception as e:
            self.show_error(f"Connection failed: {str(e)}")
    
    def show_error(self, message):
        """Display error popup"""
        content = BoxLayout(orientation='vertical', padding=10)
        content.add_widget(Label(text=message))
        close_btn = Button(text='Close', size_hint_y=0.3)
        content.add_widget(close_btn)
        
        popup = Popup(title='Error', content=content, size_hint=(0.8, 0.4))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()


class RobotManagerScreen(Screen):
    """Screen for adding and managing robots"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Title bar
        title_bar = BoxLayout(size_hint_y=0.1)
        title_bar.add_widget(Label(text='Robot Manager', font_size='20sp'))
        back_btn = Button(text='Disconnect', size_hint_x=0.3)
        back_btn.bind(on_press=self.disconnect)
        title_bar.add_widget(back_btn)
        layout.add_widget(title_bar)
        
        # Robot list
        list_label = Label(text='Available Robots:', size_hint_y=0.08)
        layout.add_widget(list_label)
        
        self.robot_list = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.robot_list.bind(minimum_height=self.robot_list.setter('height'))
        
        scroll = ScrollView(size_hint_y=0.35)
        scroll.add_widget(self.robot_list)
        layout.add_widget(scroll)
        
        # Add robot form
        form = GridLayout(cols=2, spacing=10, size_hint_y=0.25)
        
        form.add_widget(Label(text='Serial Number:'))
        self.serial_input = TextInput(multiline=False, input_filter='int')
        form.add_widget(self.serial_input)
        
        form.add_widget(Label(text='Client ID:'))
        self.client_input = TextInput(text='1', multiline=False, input_filter='int')
        form.add_widget(self.client_input)
        
        form.add_widget(Label(text='Response ID:'))
        self.resp_input = TextInput(text='1', multiline=False, input_filter='int')
        form.add_widget(self.resp_input)
        
        layout.add_widget(form)
        
        # Buttons
        btn_layout = GridLayout(cols=2, spacing=10, size_hint_y=0.15)
        
        add_btn = Button(text='Add Robot', background_color=(0.2, 0.6, 0.2, 1))
        add_btn.bind(on_press=self.add_robot)
        btn_layout.add_widget(add_btn)
        
        discover_btn = Button(text='Auto Discover', background_color=(0.2, 0.4, 0.6, 1))
        discover_btn.bind(on_press=self.discover_robots)
        btn_layout.add_widget(discover_btn)
        
        layout.add_widget(btn_layout)
        
        # Status
        self.status_label = Label(text='', size_hint_y=0.07)
        layout.add_widget(self.status_label)
        
        self.add_widget(layout)
    
    def on_enter(self):
        """Called when screen is displayed"""
        self.refresh_robot_list()
    
    def refresh_robot_list(self):
        """Update the robot list display"""
        self.robot_list.clear_widgets()
        app = App.get_running_app()
        
        if not hasattr(app, 'radio') or not app.radio:
            return
        
        robots = app.radio.avalible_bots()
        
        if not robots:
            self.robot_list.add_widget(
                Label(text='No robots added', color=(1, 1, 0, 1))
            )
            return
        
        for idx, robot in enumerate(robots):
            btn_layout = BoxLayout(size_hint_y=None, height=60, spacing=5)
            
            # Robot info
            info = f"SN: {robot['serial number']} | ID: {robot['client ID']}"
            info_label = Label(text=info, size_hint_x=0.6)
            btn_layout.add_widget(info_label)
            
            # Select button
            select_btn = Button(
                text='Control',
                size_hint_x=0.2,
                background_color=(0.2, 0.6, 0.2, 1)
            )
            select_btn.bind(on_press=lambda x, i=idx: self.select_robot(i))
            btn_layout.add_widget(select_btn)
            
            # Remove button
            remove_btn = Button(
                text='Remove',
                size_hint_x=0.2,
                background_color=(0.8, 0.2, 0.2, 1)
            )
            remove_btn.bind(on_press=lambda x, i=idx: self.remove_robot(i))
            btn_layout.add_widget(remove_btn)
            
            self.robot_list.add_widget(btn_layout)
    
    def add_robot(self, instance):
        """Add a robot to the system"""
        app = App.get_running_app()
        
        try:
            serial = int(self.serial_input.text)
            client_id = int(self.client_input.text)
            resp_id = int(self.resp_input.text)
            
            if app.radio.add_bot(serial, client_id, resp_id):
                self.status_label.text = f'Robot {serial} added'
                self.status_label.color = (0, 1, 0, 1)
                self.refresh_robot_list()
                
                # Clear inputs
                self.serial_input.text = ''
                self.client_input.text = '1'
                self.resp_input.text = '1'
            
        except ValueError:
            self.status_label.text = 'Invalid input values'
            self.status_label.color = (1, 0, 0, 1)
        except Exception as e:
            self.status_label.text = f'Error: {str(e)}'
            self.status_label.color = (1, 0, 0, 1)
    
    def discover_robots(self, instance):
        """Auto-discover robots on all channels"""
        self.status_label.text = 'Discovering robots...'
        self.status_label.color = (1, 1, 0, 1)
        
        def discover_thread():
            try:
                app = App.get_running_app()
                app.radio.discover_robots()
                Clock.schedule_once(lambda dt: self.discovery_complete(), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self.discovery_failed(str(e)), 0)
        
        threading.Thread(target=discover_thread, daemon=True).start()
    
    def discovery_complete(self):
        """Called when discovery finishes"""
        self.status_label.text = 'Discovery complete'
        self.status_label.color = (0, 1, 0, 1)
        self.refresh_robot_list()
    
    def discovery_failed(self, error):
        """Called when discovery fails"""
        self.status_label.text = f'Discovery failed: {error}'
        self.status_label.color = (1, 0, 0, 1)
    
    def select_robot(self, index):
        """Select robot and go to control screen"""
        app = App.get_running_app()
        app.radio.set_current_bot(index)
        self.manager.current = 'control'
    
    def remove_robot(self, index):
        """Remove robot from list"""
        app = App.get_running_app()
        if hasattr(app.radio, 'bots'):
            app.radio.bots.pop(index)
            self.refresh_robot_list()
    
    def disconnect(self, instance):
        """Disconnect radio and return to connection screen"""
        app = App.get_running_app()
        if hasattr(app, 'radio') and app.radio:
            app.radio.close()
            app.radio = None
        self.manager.current = 'connection'


class ControlScreen(Screen):
    """Main robot control screen with joystick and buttons"""
    
    robot_info = StringProperty('No robot selected')
    is_powered = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        main_layout = BoxLayout(orientation='vertical', padding=5, spacing=5)
        
        # Top bar
        top_bar = BoxLayout(size_hint_y=0.08)
        back_btn = Button(text='Back', size_hint_x=0.2)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'robot_manager'))
        top_bar.add_widget(back_btn)
        
        self.info_label = Label(text=self.robot_info, font_size='16sp')
        top_bar.add_widget(self.info_label)
        
        main_layout.add_widget(top_bar)
        
        # Main control area
        control_area = BoxLayout(orientation='horizontal', spacing=10)
        
        # Left panel - Movement controls
        left_panel = BoxLayout(orientation='vertical', size_hint_x=0.5, spacing=10)
        
        # Joystick area
        joystick_label = Label(text='Movement Control', size_hint_y=0.1, font_size='18sp')
        left_panel.add_widget(joystick_label)
        
        # Directional pad
        dpad = GridLayout(cols=3, spacing=5, size_hint_y=0.6)
        
        dpad.add_widget(Label())  # Empty corner
        up_btn = Button(text='↑\nForward', background_color=(0.3, 0.5, 0.8, 1))
        up_btn.bind(on_press=lambda x: self.move('forward'))
        up_btn.bind(on_release=lambda x: self.stop_move())
        dpad.add_widget(up_btn)
        dpad.add_widget(Label())  # Empty corner
        
        left_btn = Button(text='←\nLeft', background_color=(0.3, 0.5, 0.8, 1))
        left_btn.bind(on_press=lambda x: self.move('left'))
        left_btn.bind(on_release=lambda x: self.stop_move())
        dpad.add_widget(left_btn)
        
        stop_btn = Button(text='STOP', background_color=(0.8, 0.2, 0.2, 1))
        stop_btn.bind(on_press=lambda x: self.stop_move())
        dpad.add_widget(stop_btn)
        
        right_btn = Button(text='→\nRight', background_color=(0.3, 0.5, 0.8, 1))
        right_btn.bind(on_press=lambda x: self.move('right'))
        right_btn.bind(on_release=lambda x: self.stop_move())
        dpad.add_widget(right_btn)
        
        dpad.add_widget(Label())  # Empty corner
        down_btn = Button(text='↓\nBackward', background_color=(0.3, 0.5, 0.8, 1))
        down_btn.bind(on_press=lambda x: self.move('backward'))
        down_btn.bind(on_release=lambda x: self.stop_move())
        dpad.add_widget(down_btn)
        dpad.add_widget(Label())  # Empty corner
        
        left_panel.add_widget(dpad)
        
        # Rotation controls
        rotation = GridLayout(cols=2, spacing=5, size_hint_y=0.2)
        
        rotate_left = Button(text='⟲ Rotate Left', background_color=(0.5, 0.4, 0.7, 1))
        rotate_left.bind(on_press=lambda x: self.move('rotate_left'))
        rotate_left.bind(on_release=lambda x: self.stop_move())
        rotation.add_widget(rotate_left)
        
        rotate_right = Button(text='⟳ Rotate Right', background_color=(0.5, 0.4, 0.7, 1))
        rotate_right.bind(on_press=lambda x: self.move('rotate_right'))
        rotate_right.bind(on_release=lambda x: self.stop_move())
        rotation.add_widget(rotate_right)
        
        left_panel.add_widget(rotation)
        
        control_area.add_widget(left_panel)
        
        # Right panel - Functions
        right_panel = BoxLayout(orientation='vertical', size_hint_x=0.5, spacing=10)
        
        functions_label = Label(text='Robot Functions', size_hint_y=0.1, font_size='18sp')
        right_panel.add_widget(functions_label)
        
        # Power control
        self.power_btn = Button(
            text='Power ON',
            size_hint_y=0.15,
            background_color=(0.2, 0.6, 0.2, 1)
        )
        self.power_btn.bind(on_press=self.toggle_power)
        right_panel.add_widget(self.power_btn)
        
        # Tower controls
        tower_label = Label(text='Tower Control', size_hint_y=0.08)
        right_panel.add_widget(tower_label)
        
        tower_btns = GridLayout(cols=1, spacing=5, size_hint_y=0.3)
        
        tower_up = Button(text='Tower UP', background_color=(0.3, 0.6, 0.3, 1))
        tower_up.bind(on_press=lambda x: self.tower_control('up'))
        tower_btns.add_widget(tower_up)
        
        tower_half = Button(text='Tower HALF', background_color=(0.5, 0.5, 0.3, 1))
        tower_half.bind(on_press=lambda x: self.tower_control('half'))
        tower_btns.add_widget(tower_half)
        
        tower_down = Button(text='Tower DOWN', background_color=(0.6, 0.4, 0.2, 1))
        tower_down.bind(on_press=lambda x: self.tower_control('down'))
        tower_btns.add_widget(tower_down)
        
        right_panel.add_widget(tower_btns)
        
        # Additional functions
        func_btns = GridLayout(cols=1, spacing=5, size_hint_y=0.25)
        
        diag_btn = Button(text='Get Diagnostics', background_color=(0.4, 0.4, 0.6, 1))
        diag_btn.bind(on_press=self.get_diagnostics)
        func_btns.add_widget(diag_btn)
        
        path_btn = Button(text='Upload Path', background_color=(0.4, 0.5, 0.5, 1))
        path_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'path'))
        func_btns.add_widget(path_btn)
        
        settings_btn = Button(text='Settings', background_color=(0.5, 0.5, 0.5, 1))
        settings_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'settings'))
        func_btns.add_widget(settings_btn)
        
        right_panel.add_widget(func_btns)
        
        # Status area
        self.status_label = Label(
            text='Ready',
            size_hint_y=0.12,
            color=(0, 1, 0, 1)
        )
        right_panel.add_widget(self.status_label)
        
        control_area.add_widget(right_panel)
        
        main_layout.add_widget(control_area)
        
        self.add_widget(main_layout)
        
        # Movement state
        self.current_movement = None
        self.movement_event = None
    
    def on_enter(self):
        """Update display when entering screen"""
        app = App.get_running_app()
        if hasattr(app, 'radio') and app.radio and app.radio.current is not None:
            bot = app.radio.bots[app.radio.current]
            self.robot_info = f"SN: {bot['serial number']} | ID: {bot['client ID']}"
            self.info_label.text = self.robot_info
    
    def move(self, direction):
        """Send movement command"""
        app = App.get_running_app()
        if not hasattr(app, 'radio') or not app.radio:
            return
        
        self.current_movement = direction
        
        # Start continuous movement
        if self.movement_event:
            self.movement_event.cancel()
        
        self.movement_event = Clock.schedule_interval(
            lambda dt: self._send_movement(direction),
            0.1  # Send command every 100ms
        )
        
        self.status_label.text = f'Moving: {direction}'
        self.status_label.color = (0, 1, 1, 1)
    
    def _send_movement(self, direction):
        """Internal method to send movement commands"""
        app = App.get_running_app()
        
        try:
            if direction == 'forward':
                app.radio.drive(x=0, y=70, z=0)
            elif direction == 'backward':
                app.radio.drive(x=0, y=-70, z=0)
            elif direction == 'left':
                app.radio.drive(x=-70, y=0, z=0)
            elif direction == 'right':
                app.radio.drive(x=70, y=0, z=0)
            elif direction == 'rotate_left':
                app.radio.drive(x=0, y=0, z=-70)
            elif direction == 'rotate_right':
                app.radio.drive(x=0, y=0, z=70)
        except Exception as e:
            self.status_label.text = f'Error: {str(e)}'
            self.status_label.color = (1, 0, 0, 1)
            self.stop_move()
    
    def stop_move(self):
        """Stop all movement"""
        if self.movement_event:
            self.movement_event.cancel()
            self.movement_event = None
        
        self.current_movement = None
        
        app = App.get_running_app()
        if hasattr(app, 'radio') and app.radio:
            try:
                app.radio.drive(x=0, y=0, z=0)
                self.status_label.text = 'Stopped'
                self.status_label.color = (1, 1, 0, 1)
            except Exception as e:
                self.status_label.text = f'Error stopping: {str(e)}'
                self.status_label.color = (1, 0, 0, 1)
    
    def toggle_power(self, instance):
        """Toggle robot power"""
        app = App.get_running_app()
        
        self.status_label.text = 'Sending power command...'
        self.status_label.color = (1, 1, 0, 1)
        
        def power_thread():
            try:
                if self.is_powered:
                    result = app.radio.power('off')
                    Clock.schedule_once(lambda dt: self.power_result(False, result), 0)
                else:
                    result = app.radio.power('on')
                    Clock.schedule_once(lambda dt: self.power_result(True, result), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self.power_error(str(e)), 0)
        
        threading.Thread(target=power_thread, daemon=True).start()
    
    def power_result(self, state, success):
        """Handle power command result"""
        if success:
            self.is_powered = state
            if state:
                self.power_btn.text = 'Power OFF'
                self.power_btn.background_color = (0.8, 0.2, 0.2, 1)
                self.status_label.text = 'Robot powered ON'
            else:
                self.power_btn.text = 'Power ON'
                self.power_btn.background_color = (0.2, 0.6, 0.2, 1)
                self.status_label.text = 'Robot powered OFF'
            self.status_label.color = (0, 1, 0, 1)
        else:
            self.status_label.text = 'Power command failed'
            self.status_label.color = (1, 0, 0, 1)
    
    def power_error(self, error):
        """Handle power command error"""
        self.status_label.text = f'Power error: {error}'
        self.status_label.color = (1, 0, 0, 1)
    
    def tower_control(self, position):
        """Control tower position"""
        app = App.get_running_app()
        
        try:
            app.radio.toggle_tower(position)
            self.status_label.text = f'Tower: {position.upper()}'
            self.status_label.color = (0, 1, 0, 1)
        except Exception as e:
            self.status_label.text = f'Tower error: {str(e)}'
            self.status_label.color = (1, 0, 0, 1)
    
    def get_diagnostics(self, instance):
        """Request and display diagnostics"""
        self.status_label.text = 'Getting diagnostics...'
        self.status_label.color = (1, 1, 0, 1)
        
        def diag_thread():
            try:
                app = App.get_running_app()
                bot = app.radio.bots[app.radio.current]
                
                data = BuildAndSendRcPacket(
                    radio=app.radio,
                    destCli=bot['client ID'],
                    respCli=bot['response ID'],
                    cycle=6,
                    joystick=EMPTY_JOYSTICK,
                    packettype='OTHER_COMMAND',
                    wait=0.5
                )
                
                if len(data) > 11:
                    if data[11] == 17:  # Diag packet
                        diag = ResponsePayload_Diag.unpack(data[11:])
                        Clock.schedule_once(lambda dt: self.show_diagnostics(diag), 0)
                    elif data[11] == 16:  # Status packet
                        status = ResponsePayload_Status.unpack(data[11:])
                        Clock.schedule_once(lambda dt: self.show_status(status), 0)
                else:
                    Clock.schedule_once(lambda dt: self.diag_failed('No data received'), 0)
                    
            except Exception as e:
                Clock.schedule_once(lambda dt: self.diag_failed(str(e)), 0)
        
        threading.Thread(target=diag_thread, daemon=True).start()
    
    def show_diagnostics(self, diag):
        """Display diagnostic data in popup"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=5)
        
        scroll = ScrollView()
        info = GridLayout(cols=2, spacing=5, size_hint_y=None)
        info.bind(minimum_height=info.setter('height'))
        
        info.add_widget(Label(text='Battery Voltage:', size_hint_y=None, height=30))
        info.add_widget(Label(text=str(diag.vbat), size_hint_y=None, height=30))
        
        info.add_widget(Label(text='Battery Temp 1:', size_hint_y=None, height=30))
        info.add_widget(Label(text=str(diag.btemp1), size_hint_y=None, height=30))
        
        info.add_widget(Label(text='Motor Temps:', size_hint_y=None, height=30))
        info.add_widget(Label(text=str(diag.otemp), size_hint_y=None, height=30))
        
        info.add_widget(Label(text='Fans:', size_hint_y=None, height=30))
        info.add_widget(Label(text=str(diag.fans), size_hint_y=None, height=30))
        
        scroll.add_widget(info)
        content.add_widget(scroll)
        
        close_btn = Button(text='Close', size_hint_y=0.2)
        content.add_widget(close_btn)
        
        popup = Popup(title='Diagnostics', content=content, size_hint=(0.9, 0.7))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
        
        self.status_label.text = 'Diagnostics retrieved'
        self.status_label.color = (0, 1, 0, 1)
    
    def show_status(self, status):
        """Display status data in popup"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=5)
        
        info = GridLayout(cols=2, spacing=5)
        
        info.add_widget(Label(text='Serial:'))
        info.add_widget(Label(text=str(status.serial)))
        
        info.add_widget(Label(text='State:'))
        info.add_widget(Label(text=str(status.state)))
        
        info.add_widget(Label(text='UTM X:'))
        info.add_widget(Label(text=str(status.utmX)))
        
        info.add_widget(Label(text='UTM Y:'))
        info.add_widget(Label(text=str(status.utmY)))
        
        info.add_widget(Label(text='Speed:'))
        info.add_widget(Label(text=str(status.speed)))
        
        info.add_widget(Label(text='GPS Info:'))
        info.add_widget(Label(text=str(status.gpsInfo)))
        
        content.add_widget(info)
        
        close_btn = Button(text='Close', size_hint_y=0.2)
        content.add_widget(close_btn)
        
        popup = Popup(title='Status', content=content, size_hint=(0.9, 0.6))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
        
        self.status_label.text = 'Status retrieved'
        self.status_label.color = (0, 1, 0, 1)
    
    def diag_failed(self, error):
        """Handle diagnostic failure"""
        self.status_label.text = f'Diag failed: {error}'
        self.status_label.color = (1, 0, 0, 1)


class PathUploadScreen(Screen):
    """Screen for creating and uploading paths/scenarios"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Top bar
        top_bar = BoxLayout(size_hint_y=0.08)
        back_btn = Button(text='Back', size_hint_x=0.2)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'control'))
        top_bar.add_widget(back_btn)
        top_bar.add_widget(Label(text='Path Upload', font_size='20sp'))
        layout.add_widget(top_bar)
        
        # Path info
        form = GridLayout(cols=2, spacing=10, size_hint_y=0.25)
        
        form.add_widget(Label(text='Path Name:'))
        self.name_input = TextInput(text='TestPath', multiline=False, max_length=12)
        form.add_widget(self.name_input)
        
        form.add_widget(Label(text='Date (YYMMDD):'))
        self.date_input = TextInput(text='241025', multiline=False, input_filter='int')
        form.add_widget(self.date_input)
        
        form.add_widget(Label(text='Time (HHMMSS):'))
        self.time_input = TextInput(text='120000', multiline=False, input_filter='int')
        form.add_widget(self.time_input)
        
        layout.add_widget(form)
        
        # Waypoints
        wp_label = Label(text='Waypoints (X, Y, Flag):', size_hint_y=0.08)
        layout.add_widget(wp_label)
        
        self.waypoint_list = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.waypoint_list.bind(minimum_height=self.waypoint_list.setter('height'))
        
        scroll = ScrollView(size_hint_y=0.35)
        scroll.add_widget(self.waypoint_list)
        layout.add_widget(scroll)
        
        # Add waypoint form
        wp_form = BoxLayout(size_hint_y=0.1, spacing=5)
        self.wp_x = TextInput(hint_text='X', multiline=False, input_filter='float')
        self.wp_y = TextInput(hint_text='Y', multiline=False, input_filter='float')
        self.wp_flag = TextInput(hint_text='Flag', text='0', multiline=False, input_filter='int')
        
        wp_form.add_widget(self.wp_x)
        wp_form.add_widget(self.wp_y)
        wp_form.add_widget(self.wp_flag)
        
        add_wp_btn = Button(text='Add', size_hint_x=0.3)
        add_wp_btn.bind(on_press=self.add_waypoint)
        wp_form.add_widget(add_wp_btn)
        
        layout.add_widget(wp_form)
        
        # Preset paths
        preset_layout = BoxLayout(size_hint_y=0.1, spacing=5)
        
        square_btn = Button(text='Square Path', background_color=(0.4, 0.5, 0.6, 1))
        square_btn.bind(on_press=self.load_square_path)
        preset_layout.add_widget(square_btn)
        
        clear_btn = Button(text='Clear All', background_color=(0.6, 0.4, 0.4, 1))
        clear_btn.bind(on_press=self.clear_waypoints)
        preset_layout.add_widget(clear_btn)
        
        layout.add_widget(preset_layout)
        
        # Upload button
        upload_btn = Button(
            text='Upload to Robot',
            size_hint_y=0.12,
            background_color=(0.2, 0.6, 0.2, 1)
        )
        upload_btn.bind(on_press=self.upload_path)
        layout.add_widget(upload_btn)
        
        # Status
        self.status_label = Label(text='', size_hint_y=0.08)
        layout.add_widget(self.status_label)
        
        self.add_widget(layout)
        
        # Waypoint storage
        self.waypoints = []
    
    def add_waypoint(self, instance):
        """Add a waypoint to the list"""
        try:
            x = float(self.wp_x.text)
            y = float(self.wp_y.text)
            flag = int(self.wp_flag.text) if self.wp_flag.text else 0
            
            self.waypoints.append((x, y, flag))
            self.refresh_waypoint_list()
            
            # Clear inputs
            self.wp_x.text = ''
            self.wp_y.text = ''
            self.wp_flag.text = '0'
            
        except ValueError:
            self.status_label.text = 'Invalid waypoint values'
            self.status_label.color = (1, 0, 0, 1)
    
    def refresh_waypoint_list(self):
        """Update waypoint display"""
        self.waypoint_list.clear_widgets()
        
        for idx, (x, y, flag) in enumerate(self.waypoints):
            wp_layout = BoxLayout(size_hint_y=None, height=40, spacing=5)
            
            info = Label(text=f"{idx+1}. X:{x:.1f} Y:{y:.1f} F:{flag}", size_hint_x=0.7)
            wp_layout.add_widget(info)
            
            remove_btn = Button(
                text='Remove',
                size_hint_x=0.3,
                background_color=(0.8, 0.2, 0.2, 1)
            )
            remove_btn.bind(on_press=lambda x, i=idx: self.remove_waypoint(i))
            wp_layout.add_widget(remove_btn)
            
            self.waypoint_list.add_widget(wp_layout)
    
    def remove_waypoint(self, index):
        """Remove waypoint from list"""
        if 0 <= index < len(self.waypoints):
            self.waypoints.pop(index)
            self.refresh_waypoint_list()
    
    def clear_waypoints(self, instance):
        """Clear all waypoints"""
        self.waypoints = []
        self.refresh_waypoint_list()
        self.status_label.text = 'Waypoints cleared'
        self.status_label.color = (1, 1, 0, 1)
    
    def load_square_path(self, instance):
        """Load a preset square path"""
        self.waypoints = [
            (0.0, 0.0, 0),
            (10.0, 0.0, 0),
            (10.0, 10.0, 0),
            (0.0, 10.0, 0),
            (0.0, 0.0, 1)
        ]
        self.refresh_waypoint_list()
        self.status_label.text = 'Square path loaded'
        self.status_label.color = (0, 1, 0, 1)
    
    def upload_path(self, instance):
        """Upload path to robot"""
        if not self.waypoints:
            self.status_label.text = 'No waypoints to upload'
            self.status_label.color = (1, 0, 0, 1)
            return
        
        self.status_label.text = 'Uploading path...'
        self.status_label.color = (1, 1, 0, 1)
        
        def upload_thread():
            try:
                app = App.get_running_app()
                bot = app.radio.bots[app.radio.current]
                
                # Create path
                path = TPathForXmit.from_waypoints(
                    name=self.name_input.text,
                    waypoints=self.waypoints,
                    pathdate=int(self.date_input.text),
                    pathtime=int(self.time_input.text)
                )
                
                # Upload
                success = send_scenario_to_robot(
                    radio=app.radio,
                    path=path,
                    client_id=bot['client ID'],
                    THeader=THeader,
                    TRadioPacket=TRadioPacket,
                    PACKET_TYPES=PACKET_TYPES,
                    TRespHeader=TRespHeader,
                    timeout=30.0
                )
                
                Clock.schedule_once(lambda dt: self.upload_result(success), 0)
                
            except Exception as e:
                Clock.schedule_once(lambda dt: self.upload_error(str(e)), 0)
        
        threading.Thread(target=upload_thread, daemon=True).start()
    
    def upload_result(self, success):
        """Handle upload result"""
        if success:
            self.status_label.text = 'Path uploaded successfully!'
            self.status_label.color = (0, 1, 0, 1)
        else:
            self.status_label.text = 'Path upload failed'
            self.status_label.color = (1, 0, 0, 1)
    
    def upload_error(self, error):
        """Handle upload error"""
        self.status_label.text = f'Upload error: {error}'
        self.status_label.color = (1, 0, 0, 1)


class SettingsScreen(Screen):
    """Settings and configuration screen"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Top bar
        top_bar = BoxLayout(size_hint_y=0.1)
        back_btn = Button(text='Back', size_hint_x=0.2)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'control'))
        top_bar.add_widget(back_btn)
        top_bar.add_widget(Label(text='Settings', font_size='20sp'))
        layout.add_widget(top_bar)
        
        # Settings form
        form = GridLayout(cols=2, spacing=10, size_hint_y=0.5)
        
        # RF Channel
        form.add_widget(Label(text='RF Channel:'))
        self.channel_spinner = Spinner(
            text='A',
            values=('A', 'B', 'C')
        )
        form.add_widget(self.channel_spinner)
        
        # Robot Client ID
        form.add_widget(Label(text='Change Robot ID:'))
        self.new_id_input = TextInput(multiline=False, input_filter='int')
        form.add_widget(self.new_id_input)
        
        # Robot RF Channel
        form.add_widget(Label(text='Robot RF Channel:'))
        self.robot_channel_spinner = Spinner(
            text='A',
            values=('A', 'B', 'C')
        )
        form.add_widget(self.robot_channel_spinner)
        
        layout.add_widget(form)
        
        # Action buttons
        btn_layout = GridLayout(cols=1, spacing=10, size_hint_y=0.3)
        
        channel_btn = Button(
            text='Change My RF Channel',
            background_color=(0.3, 0.5, 0.6, 1)
        )
        channel_btn.bind(on_press=self.change_radio_channel)
        btn_layout.add_widget(channel_btn)
        
        id_btn = Button(
            text='Change Robot ID',
            background_color=(0.5, 0.4, 0.6, 1)
        )
        id_btn.bind(on_press=self.change_robot_id)
        btn_layout.add_widget(id_btn)
        
        robot_channel_btn = Button(
            text='Change Robot RF Channel',
            background_color=(0.4, 0.5, 0.5, 1)
        )
        robot_channel_btn.bind(on_press=self.change_robot_channel)
        btn_layout.add_widget(robot_channel_btn)
        
        layout.add_widget(btn_layout)
        
        # Status
        self.status_label = Label(text='', size_hint_y=0.1)
        layout.add_widget(self.status_label)
        
        self.add_widget(layout)
    
    def change_radio_channel(self, instance):
        """Change our radio's RF channel"""
        try:
            app = App.get_running_app()
            channel = self.channel_spinner.text
            app.radio.set_rf(channel)
            
            self.status_label.text = f'Changed to channel {channel}'
            self.status_label.color = (0, 1, 0, 1)
        except Exception as e:
            self.status_label.text = f'Error: {str(e)}'
            self.status_label.color = (1, 0, 0, 1)
    
    def change_robot_id(self, instance):
        """Change the robot's client ID"""
        try:
            app = App.get_running_app()
            new_id = int(self.new_id_input.text)
            
            if 1 <= new_id <= 15:
                app.radio.change_bot_id(new_id)
                self.status_label.text = f'Robot ID changed to {new_id}'
                self.status_label.color = (0, 1, 0, 1)
            else:
                self.status_label.text = 'ID must be 1-15'
                self.status_label.color = (1, 0, 0, 1)
                
        except ValueError:
            self.status_label.text = 'Invalid ID value'
            self.status_label.color = (1, 0, 0, 1)
        except Exception as e:
            self.status_label.text = f'Error: {str(e)}'
            self.status_label.color = (1, 0, 0, 1)
    
    def change_robot_channel(self, instance):
        """Change the robot's RF channel"""
        try:
            app = App.get_running_app()
            channel = self.robot_channel_spinner.text
            app.radio.change_bot_rf(channel)
            
            self.status_label.text = f'Robot moved to channel {channel}'
            self.status_label.color = (0, 1, 0, 1)
        except Exception as e:
            self.status_label.text = f'Error: {str(e)}'
            self.status_label.color = (1, 0, 0, 1)


class VRCMApp(App):
    """Main application class"""
    
    def build(self):
        """Build the application UI"""
        # Set window properties
        Window.clearcolor = (0.1, 0.1, 0.1, 1)
        
        # Create screen manager
        sm = ScreenManager()
        
        # Add all screens
        sm.add_widget(ConnectionScreen(name='connection'))
        sm.add_widget(RobotManagerScreen(name='robot_manager'))
        sm.add_widget(ControlScreen(name='control'))
        sm.add_widget(PathUploadScreen(name='path'))
        sm.add_widget(SettingsScreen(name='settings'))
        
        return sm
    
    def on_stop(self):
        """Clean up when app closes"""
        if hasattr(self, 'radio') and self.radio:
            try:
                self.radio.close()
            except:
                pass


if __name__ == '__main__':
    VRCMApp().run()
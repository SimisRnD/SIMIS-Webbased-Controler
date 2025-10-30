from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.core.window import Window
from kivy.clock import Clock

# Uncomment these lines after installing kivy_garden.mapview
from kivy_garden.mapview import MapView, MapMarker

class Joystick(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.outer_radius = 80
        self.inner_radius = 30
        self.center_pos = [0, 0]
        self.touch_pos = [0, 0]
        
        with self.canvas:
            # Outer circle (boundary)
            Color(0, 0.8, 1, 0.3)
            self.outer_circle = Ellipse(size=(self.outer_radius*2, self.outer_radius*2))
            
            # Cross lines
            Color(0, 0.8, 1, 0.5)
            self.line_h = Line(points=[0, 0, 0, 0], width=1)
            self.line_v = Line(points=[0, 0, 0, 0], width=1)
            
            # Inner circle (stick)
            Color(0, 1, 1, 0.8)
            self.inner_circle = Ellipse(size=(self.inner_radius*2, self.inner_radius*2))
        
        self.bind(pos=self.update_graphics, size=self.update_graphics)
    
    def update_graphics(self, *args):
        self.center_pos = [self.center_x, self.center_y]
        
        # Update outer circle
        self.outer_circle.pos = (self.center_x - self.outer_radius, 
                                 self.center_y - self.outer_radius)
        
        # Update cross lines
        self.line_h.points = [self.center_x - self.outer_radius, self.center_y,
                              self.center_x + self.outer_radius, self.center_y]
        self.line_v.points = [self.center_x, self.center_y - self.outer_radius,
                              self.center_x, self.center_y + self.outer_radius]
        
        # Update inner circle
        self.inner_circle.pos = (self.touch_pos[0] - self.inner_radius,
                                 self.touch_pos[1] - self.inner_radius)
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.update_stick_position(touch.pos)
            return True
        return super().on_touch_down(touch)
    
    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            self.update_stick_position(touch.pos)
            return True
        return super().on_touch_move(touch)
    
    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            self.touch_pos = self.center_pos[:]
            self.update_graphics()
            return True
        return super().on_touch_up(touch)
    
    def update_stick_position(self, pos):
        dx = pos[0] - self.center_pos[0]
        dy = pos[1] - self.center_pos[1]
        dist = (dx**2 + dy**2)**0.5
        
        if dist > self.outer_radius - self.inner_radius:
            ratio = (self.outer_radius - self.inner_radius) / dist
            dx *= ratio
            dy *= ratio
        
        self.touch_pos = [self.center_pos[0] + dx, self.center_pos[1] + dy]
        self.update_graphics()

class MapWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.grid_size = 50
        
        with self.canvas.before:
            Color(0.05, 0.05, 0.1, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)
        
        with self.canvas:
            Color(0, 0.5, 0.7, 0.3)
            self.grid_lines = []
        
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        self.rover_pos = [0.5, 0.5]  # Normalized position
    
    def update_graphics(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
        
        self.canvas.remove_group('grid')
        self.canvas.remove_group('rover')
        
        with self.canvas:
            Color(0, 0.5, 0.7, 0.3)
            # Vertical lines
            for i in range(0, int(self.width), self.grid_size):
                Line(points=[self.x + i, self.y, self.x + i, self.y + self.height], 
                     width=1, group='grid')
            # Horizontal lines
            for i in range(0, int(self.height), self.grid_size):
                Line(points=[self.x, self.y + i, self.x + self.width, self.y + i], 
                     width=1, group='grid')
            
            # Draw rover marker
            Color(1, 0.3, 0, 1)
            rover_x = self.x + self.width * self.rover_pos[0]
            rover_y = self.y + self.height * self.rover_pos[1]
            Ellipse(pos=(rover_x - 8, rover_y - 8), size=(16, 16), group='rover')
            Color(1, 0.5, 0, 0.5)
            Ellipse(pos=(rover_x - 15, rover_y - 15), size=(30, 30), group='rover')
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.update_rover_position(touch.pos)
            return True
        return super().on_touch_down(touch)
    
    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            self.update_rover_position(touch.pos)
            return True
        return super().on_touch_move(touch)
    
    def update_rover_position(self, pos):
        self.rover_pos[0] = (pos[0] - self.x) / self.width
        self.rover_pos[1] = (pos[1] - self.y) / self.height
        self.rover_pos[0] = max(0, min(1, self.rover_pos[0]))
        self.rover_pos[1] = max(0, min(1, self.rover_pos[1]))
        self.update_graphics()

# ALTERNATIVE: Real Map Widget using Kivy Garden MapView
# Uncomment this class and comment out MapWidget above after installing kivy_garden.mapview

class RealMapWidget(MapView):
    def __init__(self, **kwargs):
        # Set initial position (latitude, longitude) - example: New York City
        super().__init__(lat=40.7128, lon=-74.0060, zoom=15, **kwargs)
        
        # Add rover marker
        self.rover_marker = MapMarker(lat=40.7128, lon=-74.0060)
        self.add_marker(self.rover_marker)
        
        # Store for touch handling
        self.marker_dragging = False
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            # Check if touching near marker for dragging
            if self.rover_marker.collide_point(*touch.pos):
                self.marker_dragging = True
                return True
        return super().on_touch_down(touch)
    
    def on_touch_move(self, touch):
        if self.marker_dragging and self.collide_point(*touch.pos):
            # Convert screen position to lat/lon and move marker
            lat, lon = self.get_latlon_at(*touch.pos, zoom=self.zoom)
            self.rover_marker.lat = lat
            self.rover_marker.lon = lon
            return True
        return super().on_touch_move(touch)
    
    def on_touch_up(self, touch):
        self.marker_dragging = False
        return super().on_touch_up(touch)


class HUDWidget(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        with self.canvas.before:
            Color(0.02, 0.02, 0.05, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)
        
        self.bind(pos=self.update_bg, size=self.update_bg)
        
        # Map background
        # self.map_widget = MapWidget(
        #     pos_hint={'x': 0.05, 'y': 0.05},
        #     size_hint=(0.6, 0.7)
        # )
        
        
        # TO USE REAL MAP: Replace above with this after installing kivy_garden.mapview
        self.map_widget = RealMapWidget(
            pos_hint={'x': 0.05, 'y': 0.05},
            size_hint=(0.6, 0.7)
        )
        self.add_widget(self.map_widget)
        
        # Top status bar
        self.rover_id = Label(
            text='[b]ROVER-01[/b]',
            markup=True,
            pos_hint={'x': 0.05, 'top': 0.98},
            size_hint=(0.3, 0.08),
            font_size='24sp',
            color=(0, 1, 1, 1),
            halign='left',
            valign='middle'
        )
        self.rover_id.bind(size=self.rover_id.setter('text_size'))
        self.add_widget(self.rover_id)
        
        # Battery indicator
        self.battery = Label(
            text='[b]BATTERY:[/b] 87%',
            markup=True,
            pos_hint={'x': 0.35, 'top': 0.98},
            size_hint=(0.3, 0.08),
            font_size='18sp',
            color=(0.3, 1, 0.3, 1),
            halign='center',
            valign='middle'
        )
        self.battery.bind(size=self.battery.setter('text_size'))
        self.add_widget(self.battery)
        
        # Speed indicator
        self.speed = Label(
            text='[b]SPEED:[/b] 0.0 m/s',
            markup=True,
            pos_hint={'x': 0.05, 'top': 0.88},
            size_hint=(0.3, 0.08),
            font_size='18sp',
            color=(1, 0.8, 0, 1),
            halign='left',
            valign='middle'
        )
        self.speed.bind(size=self.speed.setter('text_size'))
        self.add_widget(self.speed)
        
        # Connection status
        self.status = Label(
            text='[b]STATUS:[/b] CONNECTED',
            markup=True,
            pos_hint={'x': 0.35, 'top': 0.88},
            size_hint=(0.3, 0.08),
            font_size='16sp',
            color=(0, 1, 0.5, 1),
            halign='center',
            valign='middle'
        )
        self.status.bind(size=self.status.setter('text_size'))
        self.add_widget(self.status)
        
        # Joystick
        self.joystick = Joystick(
            pos_hint={'right': 0.95, 'center_y': 0.3},
            size_hint=(None, None),
            size=(200, 200)
        )
        self.add_widget(self.joystick)
        
        # Joystick label
        self.joy_label = Label(
            text='MOVEMENT',
            pos_hint={'right': 0.95, 'y': 0.08},
            size_hint=(0.2, 0.05),
            font_size='14sp',
            color=(0, 0.8, 1, 0.8),
            halign='center'
        )
        self.add_widget(self.joy_label)
        
        # Coordinates display
        self.coords = Label(
            text='X: 0.00  Y: 0.00',
            pos_hint={'x': 0.05, 'y': 0.01},
            size_hint=(0.3, 0.05),
            font_size='14sp',
            color=(0, 0.8, 1, 0.8),
            halign='left'
        )
        self.add_widget(self.coords)
    
    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

class RoverHUDApp(App):
    def build(self):
        Window.clearcolor = (0.02, 0.02, 0.05, 1)
        return HUDWidget()

if __name__ == '__main__':
    RoverHUDApp().run()
import serial
import serial.tools.list_ports
from queue import Queue
import threading
import time
import struct


def num_to_letter(num):
    if 1 <= num <= 26:
        return chr(num + 96)  # 97 ('a') - 1 = 96
    else:
        return None  
    

class ThreadSafeCounter:
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()

    def increment(self):
        with self.lock:
            self.value += 1
            return self.value

    def get_value(self):
        with self.lock:
            return self.value



TErrorCodeDict = {
    #Motors
    0x0001: "ERR_MOT1",
    0x0002: "ERR_MOT2",
    0x0004: "ERR_MOT3",
    0x0008: "ERR_MOT4",

    #Coms
    0x0010: "ERR_RADIO_HW",
    0x0020: "ERR_RADIO_PROTO",

    #
    0x0040: "ERR_FAN_TOP",
    0x0080: "ERR_FAN_BOT",
    0x0100: "ERR_NO_BATTERY",


    0x0200: "ERR_NO_HITDET",
    0x0400: "ERR_NO_RISER",
    0x0800: "ERR_NO_GPS1",
    0x1000: "ERR_NO_GPS2",
    0x2000: "ERR_MOT_NOTRDY",
    0x4000: "ERR_FAN_PDB",
}

ErrorDiscriptor = {
    "ERR_MOT1": "No response from motor 1",
    "ERR_MOT2": "No response from motor 2",
    "ERR_MOT3": "No response from motor 3",
    "ERR_MOT4": "No response from motor 4",
    "ERR_RADIO_HW" : "no hardware response from radio",
    "ERR_RADIO_PROTO" : "protocol error in incoming radio packet",
    "ERR_RADIO_PROTO" : "protocol error in incoming radio packet",

}
def get_errors(errorbits):
    """Determine which errors are present in the given bitmask."""
    return [TErrorCodeDict[bit] for bit in TErrorCodeDict if errorbits & bit]

def getPortDetails():
    ports = serial.tools.list_ports.comports()
    port_details = [
        (port.device, port.description, port.hwid) for port in ports
    ]
    
    return port_details

def usbPorts():
    ports = getPortDetails()
    usb_ports = []
    for port, description, hwid in ports:
        if 'usb' in hwid.lower():
            usb_ports.append(port)
    return usb_ports

def openPort(port=usbPorts()[0],baud=115200,timeout=0.5,writeout=0.5):
    print(f'USB:{port}')
    port = serial.Serial(port=port,baudrate=baud,
                         timeout=timeout,write_timeout=writeout)
    return port


class Decoders:

    def __init__(self):
        self.headers = {'request':0,
               'system':self.system,
               'hit':self.hit,
               'gps':self.gps,
               'bat1':self.battery1,
               'bat2':5,
               'get_scen_info':self.paths,
               'put_scen_info':self.upload_request,
               'upload_scen':self.upload_reponse,
               'up':10,
               'down':11,
               'half':12,
               'joy':13,
               'On/Off':14,
               }

    def decode(self,packet_type,packet):
        return self.headers[packet_type](packet)
    
    def upload_reponse(self,pack):
        # print('pack',pack)
        d = [element for element in pack]
        data= {}
        data['packet 0:'] = pack[0]
        data['paylength'] = pack[1]
        data['serial'] = (pack[3] << 8) | (pack[2] & 0xFF)
        data['inventory_idx'] = pack[4]
        data['next_packet'] = pack[5]

        
        print('RAW PACKET:',d)
        print(data)
        return data

    def system(self,pack):
        data = {}
        data['paylength'] = pack[1]
        data['serial'] = (pack[3] << 8) | (pack[2] & 0xFF)
        data['clientId'] = pack[4]
        data['state'] = pack[5]
        data['errorbits'] = get_errors((pack[4+3] << 8) | (pack[4+2]&0xFF))
        return data
    
    def hit(self,pack):
        data = {}
        data['paylength'] = pack[1]
        data['serial'] = (pack[3] << 8) | (pack[2] & 0xFF)
        data['hitThreshold'] = pack[4]
        data['hitTimeLimit'] = pack[5]
        data['HdSensitivity'] = pack[6]
        data['hitPauseTime'] = pack[7]
        data['hit_zone_data'] = pack[8]
        data['zonesEnable'] = bool(pack[9])
        return data
    
    def gps(self,pack):
        data = {}
        data['paylength'] = pack[1]
        data['serial'] = (pack[3] << 8) | (pack[2] & 0xFF)
        raw_utmX = ((pack[4+3] << 24) | (pack[4+2] << 16) | (pack[4+1] << 8) | (pack[4+0] & 0xFF))
        raw_utmY = ((pack[4+7] << 24) | (pack[4+6] << 16) | (pack[4+5] << 8) | (pack[4+4] & 0xFF))
        data['utmX'] = raw_utmX / 10.
        data['utmY'] = raw_utmY / 10.
        data['utmZone'] = [pack[4+8],pack[4+9],pack[4+10],pack[4+11]]
        data['numSat'] = pack[4+12]
        data['gpsFix'] = pack[4+13]
        data['COG'] = pack[4+14]
        data['speed'] = pack[4+15]
        return data
    
    def battery1(self,pack):
        data = {}
        data['paylength'] = pack[1]
        data['serial'] = (pack[3] << 8) | (pack[2] & 0xFF)
        data['bvolt'] = [((pack[4+1] << 8) | (pack[4+0] & 0xFF)),((pack[4+3] << 8) | (pack[4+2] & 0xFF))]
        data['bcap'] = [pack[4+4],pack[4+5],pack[4+6]]
        data['bcur'] = [((pack[4+8] << 8) | (pack[4+7] & 0xFF)),((pack[4+10] << 8) | (pack[4+9] & 0xFF)),((pack[4+12] << 8) | (pack[4+11] & 0xFF))]
        return data
    
    def paths(self,pack):
        data = {}
        payload = pack[4:]
        data['paylength'] = pack[1]
        data['serial'] = (pack[3] << 8) | (pack[2] & 0xFF)
        data['cycle'] = payload[0]
        data['Number of Paths'] = payload[1]

        # data['Name:'] = [i for i in payload[:]]

        return data
    
    def upload_request(self,pack):
        data = {}
        
        payload = pack[4:]
        
        data['paylength'] = pack[1]
        data['serial'] = (pack[3] << 8) | (pack[2] & 0xFF)
        data['Request Type'] = payload[0]
        data['cycle'] = payload[1]

        # data['Name:'] = [i for i in payload[1:]]

        return data
    
    def debug(self,pack):
        data = {}
        data['header']=pack[0]
        data['type'] = pack[1]
        payload = pack[4:]
        data['paylength'] = pack[1]
        data['serial'] = (pack[3] << 8) | (pack[2] & 0xFF)
        data['Request Type'] = payload[0]
        data['cycle'] = payload[1]

        # data['Name:'] = [i for i in payload[1:]]

        return data
    
    
        


class PacketBuilder:
    headers = {'usb':0xD,
                'request':0,
               'system':1,
               'hit':2,
               'gps':3,
               'bat1':4,
               'bat2':5,
               'get_scen_info':6,
               'put_scen_info':8,
               'upload_scen':9,
               'up':10,
               'down':11,
               'half':12,
               'joy':13,
               'On/Off':14,
               'select_target':15,
               }
    paylen = 2
    joy_paylen = 6
    
    def get(self,data='request',cycle=1,serial=1201,jx=0,jy=0,jz=0,jb=0,waypoints=[],target=1):
        if data!= 'upload_scen':
            paylen = self.paylen if data!='joy' else self.joy_paylen
            # paylen = self.paylen + 1 if data=='select_target' else 0
            packet_ = bytearray(4+paylen)
            packet_[0] = self.headers['usb']
            packet_[1] = paylen
            packet_[2] = ((serial >> 0) & 0xF)
            packet_[3] = ((serial>> 4) & 0xF)
            packet_[4] = self.headers[data]
            packet_[5] = cycle
            if data == 'joy':
                packet_[6] = (jx + 100)
                packet_[7] = (jy + 100) 
                packet_[8] = (jz + 100)
                packet_[9] = jb
            elif data == 'select_target':
                packet_[6] = target
        else:
            #(type) (totat # of packets, current packet, ) (9 data point long payload)
            paylen = 1+2+9
            packet_ = bytearray(4+paylen)
            packet_[0] = self.headers['usb']
            packet_[1] = paylen
            packet_[2] = ((serial >> 0) & 0xF)
            packet_[3] = ((serial>> 4) & 0xF)
            packet_[4] = self.headers[data]
            packet_[5] = len(waypoints)

        return packet_
    
    def waypointer(self, name, date, time, origin, waypoints):
        serial = 1204
        packets = []

        # === Build packets 0–8 as before ===
        padded_name = name.encode("utf-8").ljust(12, b'\x00')

        def base_packet(idx, data_bytes):
            paylen = 1 + 2 + len(data_bytes)
            p = bytearray(4 + paylen)
            p[0] = self.headers['usb']
            p[1] = paylen
            p[2] = ((serial >> 0) & 0xF)
            p[3] = ((serial >> 4) & 0xF)
            p[4] = self.headers['upload_scen']
            p[5] = len(waypoints) + 9
            p[6] = len(waypoints) + 8
            p[7] = idx
            p[8:] = data_bytes
            return p

        packets.append(base_packet(0, padded_name[:6]))
        packets.append(base_packet(1, padded_name[6:12]))
        packets.append(base_packet(2, struct.pack('<I', date) + struct.pack('<I', time)))
        packets.append(base_packet(3, struct.pack('<f', origin[0])))
        packets.append(base_packet(4, b'\x00' * 8))
        packets.append(base_packet(5, struct.pack('<f', origin[1])))
        packets.append(base_packet(6, b'\x00' * 8))
        packets.append(base_packet(7, struct.pack('<f', origin[2]) + struct.pack('<f', origin[3])))
        packets.append(base_packet(8, struct.pack('<H', len(waypoints)) + struct.pack('<H', 0)))

        # === Waypoint packets: each 12 bytes (x, y, flag) ===
        for i, (x, y, flag) in enumerate(waypoints):
            payload = struct.pack('<f', x) + struct.pack('<f', y) + struct.pack('<f', flag)
            packets.append(base_packet(9 + i, payload))

        return packets


    
class RadioStack:
    def __init__(self,**kwargs):
        self.messages = {}
        self.port = openPort(**kwargs)

        #Since application is threaded make sure the interactions at the port are thread safe
        self.queue = Queue()
        self.count = ThreadSafeCounter()
        self.lock  = threading.Lock()
    
    def write(self,packet):
        self.port.write(packet)
    
    def read(self):
        return self.port.readline()
    
    def _send(self,packet):
        id_ = self.count.increment()
        self.queue.put((id_,packet))
        return id_
    
    def request(self,packet,sleep=0,clear=False):
        id_ = self._send(packet)
        self.send(sleeper=sleep,clear=clear)
        while True:
            with self.lock:
                if id_ in self.messages:
                    return self.messages.pop(id_)             

    def send(self,sleeper=0,clear=False):
        if clear:
            if not self.queue.empty():
                while not self.queue.empty():
                    id_,packet = self.queue.get()
                    if not self.queue.empty():
                        self.messages[id_] = 'N/A'

                with self.lock:
                    # self.queue.clear()
                    self.write(packet)
                    message = self.read()
                
                    self.messages[id_] = message
                    

        else:
            while True:
                if not self.queue.empty():
                    id_,packet = self.queue.get()
                    
                    with self.lock:
                        
                        self.write(packet)
                        time.sleep(sleeper)
                        message = self.read()
                    
                        self.messages[id_] = message
                    return 0
                else:
                    return 0


class Requests:
    def __init__(self,**kwargs):
        #USB/Serial interface with radio
        self.radio = RadioStack(**kwargs)

        #Builds the packes to make data requests and commands
        self.pb = PacketBuilder()

        #Decodes the data recieved
        self.decoder = Decoders()
    
    def request(self,packet_type='system',**kwargs):
        packet = self.pb.get(packet_type,**kwargs)
        response = self.radio.request(packet)
        return self.decoder.decode(packet_type,response)
    
    def command(self,packet_type='up',**kwargs):
        packet = self.pb.get(packet_type,**kwargs)
        response = self.radio.request(packet)
        return response
    
    def supercommand(self,packet_type='up',**kwargs):
        packet = self.pb.get(packet_type,**kwargs)
        response = self.radio.request(packet,clear=True)
        return response
    
    def uploader(self,name,date, time, origin,waypoint):
        packets = self.pb.waypointer(name,date, time, origin,waypoint)
        n = 0
        double = 0
        retries = 0
        while n < len(packets) and retries<20:
            response = self.radio.request(packets[n],0.5)
            
            try:
                decoded_msg = self.decoder.decode('upload_scen',response)
                serial_ = int(decoded_msg.get('serial',1))
                if serial_ != 0 and n<10:
                    if serial ==2:
                        n+=1
                        print(f'Packet {n}/{len(packets)-1} accepted')
                        break
                    retries+=1
                    self.radio.read()
                    self.radio.read()
                    
                elif double == 0:
                    retries = 0
                    n+=1
                    print(f'Packet {n}/{len(packets)-1} accepted')
                
                if n>=10:
                    double+=1
                    double = double%2

            except Exception as e:
                if n == len(packets)-1:
                    break
                retries+=1
           
        if retries ==0:
            return True
        else:
            return False


    

class Htt(Requests):
    def __init__(self, **kwargs):
        self.sentZero = False
        super().__init__(**kwargs)
    
    def info_system(self,serial=1204):
        return self.request('system',serial=serial)
    
    def info_gps(self,serial=1204):
        return self.request('gps',serial=serial)
    
    def info_hit(self,serial=1204):
        return self.request('hit',serial=serial)
    
    def info_battery(self,serial=1204):
        return self.request('bat1',serial=serial)
    
    def info_paths(self,serial=1204):
        return self.request('get_scen_info',serial=serial,cycle=255)
    
    def info_upload(self,serial=0000):
        return self.request('put_scen_info',serial=serial)
    
    def cmd_down(self,serial=1204):
        return self.command('down',serial=serial)
    
    def cmd_up(self,serial=1204):
        return self.command('up',serial=serial)
    
    def cmd_half(self,serial=1204):
        return self.command('half',serial=serial)
    
    def cmd_onoff(self,serial=1204):
        info = self.command('On/Off',serial=serial)
        time.sleep(5)
        return info
    
    def cmd_drive(self,jx=0,jy=-0,jz=0,serial=1204):
        if jx ==  0 and jy == 0 and jz==0 and self.sentZero:
            return 0
        elif jx ==  0 and jy == 0 and jz==0 and  (not self.sentZero):
            self.sentZero = True
        else:
            self.sentZero = False
        return self.command('joy',jx=jx,jy=jy,jz=jz,serial=serial)
    
    def cmd_select(self,status=0,serial=1204):
        return self.command('joy',jb=status,serial=serial)
    
    def cmd_twist(self,dir=1,serial=1204):
        jz = int(dir*100)
        return self.command('joy',jz=jz,serial=serial)
    
    def cmd_upload(self,name,date, time, origin,waypoints):
        return self.uploader(name,date, time, origin,waypoints)
    
    def cmd_stop(self):
        return self.supercommand('joy')
    
    def cmd_select_target(self,target=1):
        return self.supercommand('select_target',target=target)

    

if __name__ == '__main__':
    #Example of HTT class
    HTT = Htt()


    # system_info = HTT.info_system()
    # [print(data,system_info[data]) for data in system_info]

    # hit_info = HTT.info_hit()
    # [print(data,hit_info[data]) for data in hit_info]

    # gps_info = HTT.info_gps(serial=1200)
    # [print(data,gps_info[data]) for data in gps_info]

    # battery_info = HTT.info_battery()
    # [print(data,battery_info[data]) for data in battery_info]

    
    # HTT.cmd_drive(0,50,0)
    
    # HTT.cmd_down()
    # HTT.cmd_half()
    # # HTT.cmd_down()
    # HTT.cmd_up()

    # paths = HTT.info_system()
    # [print(data,paths[data]) for data in paths]
    waypointexample ={'name':'Trents',
                      'date':250401,
                      'time':130701,
                      'origin': (36.77975007214028, 13.460526464700607, 362624.9082361866, 4071544.9471976613), 
                      'waypoints':  [(362624.9082361866, 4071544.9471976613, 0), 
                                     (362638.46262458985, 4071553.783608709, 0), 
                                     (362631.3790374973, 4071560.0927708508, 0), 
                                     (362622.1192670587, 4071550.2341624564, 0),
                                     (362624.9082361866, 4071544.9471976613, 0), 
                                     (362638.46262458985, 4071553.783608709, 0), 
                                     (362631.3790374973, 4071560.0927708508, 0), 
                                     (362622.1192670587, 4071550.2341624564, 0)]}
    HTT.cmd_upload(**waypointexample)

    


    

    


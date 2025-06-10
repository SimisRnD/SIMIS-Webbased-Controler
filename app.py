from flask import Flask, render_template, jsonify, request, send_file, Response, send_from_directory, redirect, url_for
from PIL import Image, ImageDraw
from genfeed import generate_frames
# import simplified_radio
from vectors_ import Vector
import time
from functools import wraps
from flask import g
from HTT import Htt
from gpstransformer import latLong2UTM, UTM2LonLat
import gen_qr

HTT = Htt()
PAUSE = False
scens = {}
last_time = time.time()

#Base requirment
def rate_limit(f):
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        global last_time
        current_time = time.time()
        print(current_time-last_time)
        if abs(current_time-last_time) < 0.25:
            # print('Too Fast')
            return {'301':'too fast'}, 301
        else:
            last_time = current_time
        return f(*args, **kwargs)
        
    return decorated_function


WAYPOINTS = {}
for i in range(1,9):
    WAYPOINTS[i] = []


def intify(x):
    print('BEFORE INTIFY',x)
    return int(round(float(x),0))

app = Flask(__name__)

# Distinct Pages
@app.route('/')
def index():
    return render_template('dashboard.html')


# Distinct Pages
@app.route('/controler')                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               
def controler():
    return render_template('controlerv2.html')


# Distinct Pages
@app.route('/connect')                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               
def connect():
    return render_template('connect.html')


# Route to download the ZIP file
@app.route('/_download')
def _download():
    return send_from_directory(
        directory='static',  # Directory where the file is stored
        path='controler.zip',   # File name
        as_attachment=True   # Forces download
    )


# Route for the homepage
@app.route('/download')
def download():
    return render_template('download.html')

# Distinct Pages
@app.route('/statistics')                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               
def statistics():
    return render_template('statistics.html')

# Joystick backend

@app.route('/_joystick', methods=['POST'])
@rate_limit
def joystick():
    data = request.get_json()
    power = data.get('POWER', '0')
    angle = data.get('ANGLE', '0')
    print(f'Power: {power}\nAngle: {angle}')
    

    joystick_v = 100*Vector(mag=float(power),theta=float(angle),deg=False)
    print(joystick_v)
    try:
        jx = -1*intify(joystick_v[0])
        jy = intify(joystick_v[1])
        jz = 0
        print('jx', float(jx),'jy ',float(jy))
        HTT.cmd_drive(jx,jy,jz,1204)
        # simplified_radio.sendJoyStickCMD(jx,jy,0)
    except Exception as e:
        print(e)
    return {'Bet':'Got it'}, 200

@app.route('/stopit', methods=['POST','GET'])
def stopit():
    HTT.cmd_stop()
    return {'Bet':'Got it'}, 200

@app.route('/_joystick_b', methods=['POST'])
def joystickb():
    data = request.get_json()
    power = data.get('POWER', '0')
    angle = data.get('ANGLE', '0')
    print(f'Power: {power}\nAngle: {angle}')
    

    joystick_v = 100*Vector(mag=float(power),theta=float(angle),deg=False)
    print(joystick_v)
    try:
        jx = -1*intify(joystick_v[0])
        jy = intify(joystick_v[1])
        jz = 0
        print('jx', float(jx),'jy ',float(jy))
        HTT.cmd_drive(jx,jy,jz,1204)
        # simplified_radio.sendJoyStickCMD(jx,jy,0)
    except Exception as e:
        print(e)
    return {'Bet':'Got it'}, 200


@app.route('/select', methods=['POST'])

def select():
    data = request.get_json()
    status = data.get('status', '0')
    
    try:
        HTT.cmd_select(status)
        
    except Exception as e:
        print(e)
    return {'Bet':'Got it'}, 200

@app.route('/twist', methods=['POST'])
def twist():
    data = request.get_json()
    dir = data.get('dir', '1')
    
    try:
        HTT.cmd_twist(dir)
        HTT.cmd_twist(0)
        
    except Exception as e:
        print(e)
    return {'Bet':'Got it'}, 200

# Joystick backend

@app.route('/_buttons', methods=['POST'])
def buttons():
    # button_map = {
    #     'down':simplified_radio.sendLowerTorsoCMD,
    #     'up':simplified_radio.sendRaiseTorsoCMD,
    #     'Mode:Shift':simplified_radio.sendHalfTorsoCMD,
    #     'Mode:RC':simplified_radio.get_all_data
    # } 

    button_map = {
        'down':HTT.cmd_down,
        'up':HTT.cmd_up,
        'Mode:Shift':HTT.cmd_half,
        'Mode:RC':HTT.info_gps,
        'Scenario:Start':HTT.cmd_onoff,
        'Targets:1':HTT.cmd_select_target,
        'Targets:2':HTT.cmd_select_target,
        'Targets:3':HTT.cmd_select_target,
        'Targets:4':HTT.cmd_select_target,
        'Targets:5':HTT.cmd_select_target,
        'Targets:6':HTT.cmd_select_target,
        'Targets:7':HTT.cmd_select_target,
        ' ':HTT.cmd_select_target,

    } 
    data = request.get_json()
    button = data.get('BUTTON', '0')
    if button != 'Mode:RC' and 'Targets' not in button:
        button_map[button]()
    elif 'Targets' in button:
        button_map[button](int(button.split(':')[1]))
    else:
        info = button_map[button]()
        [print(data, info[data]) for data in info]

    print('Button: ',button)
    return {'Bet':f'Got it, button {button}'}, 200

# Joystick backend
@app.route('/_gps/add_way_point', methods=['POST'])
def add_waypoints():
    global WAYPOINTS
    data = request.get_json()
    target = data.get('TAR', None)
    lat = float(data.get('LAT', None))
    lon = float(data.get('LON',None))+90
    utmX, utmY = latLong2UTM(lat,lon)
    
    if WAYPOINTS.get(target,None) == None:
        WAYPOINTS[target] = {'name':target,
                         'date':250429,
                      'time':120222,
                      'origin':(lat,lon,utmX,utmY),
                      'waypoints':[]}
    
    if target and lat and lon:
        WAYPOINTS[target]['waypoints'].append((utmX,utmY,1))
    print('Added: ',(target,lat,lon))

    
    return {'Bet':f'{target}:({lat},{lon})'}, 200


# Joystick backend
@app.route('/_gps/make_scen', methods=['POST'])
def upload_scen():
    global WAYPOINTS, PAUSE
    data = request.get_json()
    target = data.get('TAR', None)
    name = data.get('NAME','DefualtName')
    WAYPOINTS[target]['name'] = name
    selected = WAYPOINTS[target]
    print(selected)
    PAUSE = True
    time.sleep(1)
    HTT.cmd_upload(**selected)
    time.sleep(5)
    PAUSE = False
    
    return {'Bet':''}, 200


@app.route('/_gps/info',methods=['GET'])
def _gps_info():
    global PAUSE
    lat,lon = 36.78021105,13.4600115
    try:
        if not PAUSE:
            print('Not pause')
            gps_info = HTT.info_gps()
            serial = gps_info['serial']
            speed = gps_info['speed']
            utmx = gps_info['utmX']
            utmy = gps_info['utmY']

        if serial != 0:
            lat,lon = UTM2LonLat(utmx,utmy)

            print(lat)
            
        else:
            pass
            
        
    except Exception as e:
        pass
    # print(lat)
    # print(lon)
    return jsonify({'lon':-90+lon,'lat':lat})



# Joystick backend
@app.route('/_power')
def power():

    
    HTT.cmd_onoff()
    return redirect(url_for('controler'))


@app.route('/video_feed')
def video_feed():
    # Return a response with the frames generated by the webcam
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# @app.route("/diag_data")
# def data():
#     return jsonify(simplified_radio.P)


if __name__ == '__main__':
    # Run Flask app with access from other devices on the network
    app.run(host='0.0.0.0', port=5000, debug=False)

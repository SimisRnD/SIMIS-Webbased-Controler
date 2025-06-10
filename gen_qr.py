import socket
import qrcode

# Function to get the local IP address of the machine
def get_local_ip():
    # Try to get the local IP address of the computer
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    return local_ip

# Replace this with the port your local app is running on
port = "5000"  # Default Flask port

# Get the local IP
local_ip = get_local_ip()

# Format the URL
local_url = f"http://{local_ip}:{port}"

# Generate the QR code for the local app
qr = qrcode.make(local_url)
qr.save("static/url_qr_code.png")
print(f"[+] QR Code generated for: {local_url}")
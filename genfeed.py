import cv2


import qrcode
image_path = "static/url_qr_code.png" 
# Specify the website URL
website_url = "http://10.162.55.154:5000/controler"

# Generate the QR code
qr = qrcode.QRCode(
    version=1,  # Controls the size of the QR Code (1 is the smallest)
    error_correction=qrcode.constants.ERROR_CORRECT_L,  # Error correction level
    box_size=10,  # Size of each box in the QR code grid
    border=4,  # Border size (minimum is 4)
)
qr.add_data(website_url)
qr.make(fit=True)

# Create and save the QR code image
img = qr.make_image(fill_color="black", back_color="white")
img.save(image_path)

print("QR Code generated and saved as 'website_qr_code.png'")



# Wi-Fi QR Code Data
wifi_data = "WIFI:T:WPA;S:TRENTS 4048;P:trent2357;H:false;"

image_path = "static/wifi_qr_code.png"
# Generate Wi-Fi QR Code
wifi_qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)
wifi_qr.add_data(wifi_data)
wifi_qr.make(fit=True)
wifi_img = wifi_qr.make_image(fill_color="black", back_color="white")
wifi_img.save(image_path)





# Load the still image
image_path = "static/not_avalible.jpg"  # Replace with your image file path
image = cv2.imread(image_path)

def generate_frames():
    while True:
        try:
            if image is None:
                raise FileNotFoundError("Image not found or unable to load.")
            
            # Encode the image in JPEG format
            _, buffer = cv2.imencode('.jpg', image)
            frame = buffer.tobytes()

            # Yield the frame to the client as an HTTP response
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except Exception as e:
            print(f"Error: {e}")
            break



import cv2
from http.server import BaseHTTPRequestHandler, HTTPServer
import io
from PIL import Image
import base64

# Function to capture image from local camera
def capture_image(camera_id):
    cap = cv2.VideoCapture(camera_id)
    ret, frame = cap.read()
    if ret:
        cap.release()
        return frame
    cap.release()
    return None

# HTTP Request Handler
class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/capture':
            # Capture image
            image = capture_image(0)
            if image is not None:
                # Convert image to JPEG
                _, jpeg = cv2.imencode('.jpg', image)
                image_bytes = jpeg.tobytes()
                base64_image = base64.b64encode(image_bytes).decode('utf-8')
                
                # Send response
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(bytes(f"data:image/jpeg;base64,{base64_image}", "utf8"))
            else:
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

def run(server_class=HTTPServer, handler_class=RequestHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting capture service on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()

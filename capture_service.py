import cv2
from http.server import BaseHTTPRequestHandler, HTTPServer
import io
from PIL import Image
import base64
from loguru import logger

def capture_image(camera_id):
    """
    Captures an image from the specified camera device.

    Args:
        camera_id: Integer ID of the camera device to capture from

    Returns:
        frame: OpenCV image frame if successful, None if capture fails
    """
    logger.debug(f"Attempting to capture image from camera ID {camera_id}")
    cap = cv2.VideoCapture(camera_id)
    ret, frame = cap.read()
    if ret:
        logger.info(f"Image captured successfully from camera ID {camera_id}")
        cap.release()
        return frame
    else:
        logger.error(f"Failed to capture image from camera ID {camera_id}")
        cap.release()
        return None

class RequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for camera capture service"""

    def do_GET(self):
        """
        Handles GET requests - captures an image from camera if /capture path is requested
        """
        logger.debug(f"Received GET request for path: {self.path}")
        if self.path == '/capture':
            logger.info("Processing capture request")
            image = capture_image(0)
            if image is not None:
                _, jpeg = cv2.imencode('.jpg', image)
                image_bytes = jpeg.tobytes()
                base64_image = base64.b64encode(image_bytes).decode('utf-8')

                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(bytes(f"data:image/jpeg;base64,{base64_image}", "utf8"))
                logger.info("Image sent successfully")
            else:
                self.send_response(500)
                self.end_headers()
                logger.error("Failed to capture image, sending 500 response")
        else:
            self.send_response(404)
            self.end_headers()
            logger.warning(f"Path not found: {self.path}, sending 404 response")

def run(server_class=HTTPServer, handler_class=RequestHandler, port=8080):
    """
    Starts the HTTP server to handle camera capture requests

    Args:
        server_class: HTTP server class to use, defaults to HTTPServer
        handler_class: Request handler class to use, defaults to RequestHandler
        port: Port number to run server on, defaults to 8080
    """
    logger.info(f"Starting capture service on port {port}...")
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logger.info("HTTP server running")
    httpd.serve_forever()

if __name__ == '__main__':
    run()

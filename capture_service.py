from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import io
import base64
from loguru import logger
from picamera import PiCamera
from time import sleep

class PicameraCapture:
    """
    PicameraCapture class to handle PiCamera for continuous frame capture.

    Attributes:
        frame (bytes): The latest captured frame in bytes.
        lock (threading.Lock): Lock to handle thread-safe access to the frame.
        running (bool): Flag to indicate if the capture loop is running.
    """
    def __init__(self):
        self.frame = None
        self.lock = threading.Lock()
        self.running = False
        self.camera = PiCamera()
        self.camera.resolution = (640, 480)
        self.camera.start_preview()
        sleep(2)  # Allow the camera to warm up

    def start(self):
        """
        Start the PiCamera capture loop in a separate thread.
        """
        self.running = True
        threading.Thread(target=self.capture_loop).start()

    def stop(self):
        """
        Stop the PiCamera capture loop.
        """
        self.running = False
        self.camera.close()

    def capture_loop(self):
        """
        Capture loop to continuously update the latest frame while the camera is running.
        """
        while self.running:
            with self.lock:
                self.update_frame()

    def update_frame(self):
        """
        Update the latest frame by capturing an image from the camera.
        """
        stream = io.BytesIO()
        self.camera.capture(stream, format='jpeg')
        stream.seek(0)
        self.frame = stream.read()

    def get_frame(self):
        """
        Get the latest captured frame in bytes.

        Returns:
            bytes: The latest captured frame.
        """
        with self.lock:
            return self.frame


class RequestHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for the image capture service.

    This handler processes GET requests to the /capture endpoint. If the request path
    is /capture, it retrieves the latest frame from the PicameraCapture instance,
    encodes it in base64, and sends it back in the response. For other paths, it
    returns a 404 response.
    """
    def do_GET(self):
        """
        Handle GET requests.

        This method processes GET requests by capturing an image if the request path is
        /capture, and sending appropriate responses based on the success or failure of
        the capture.
        """
        logger.debug(f"Received GET request for path: {self.path}")
        if self.path == '/capture':
            logger.info("Processing capture request")
            frame = picamera_capture.get_frame()
            if frame is not None:
                base64_image = base64.b64encode(frame).decode('utf-8')
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


def run(server_class=HTTPServer, handler_class=RequestHandler, port=8080):
    """
    Run the HTTP server for the image capture service.

    This function initializes and starts the HTTP server on the specified port, using the
    specified server and handler classes.

    Args:
        server_class (type): The class to use for the HTTP server.
        handler_class (type): The class to use for handling HTTP requests.
        port (int): The port on which to run the HTTP server.
    """
    logger.info(f"Starting capture service on port {port}...")
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logger.info("HTTP server running")
    httpd.serve_forever()

if __name__ == '__main__':
    picamera_capture = PicameraCapture()
    picamera_capture.start()
    try:
        run()
    except KeyboardInterrupt:
        pass
    finally:
        picamera_capture.stop()

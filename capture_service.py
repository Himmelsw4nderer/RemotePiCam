import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import io
import base64
from loguru import logger

# Initialize GStreamer
Gst.init(None)

class GStreamerCapture:
    """
    GStreamerCapture class to handle GStreamer pipeline for continuous frame capture.

    Attributes:
        frame (bytes): The latest captured frame in bytes.
        pipeline (Gst.Pipeline): The GStreamer pipeline for video capture.
        bus (Gst.Bus): The GStreamer bus to handle messages from the pipeline.
        lock (threading.Lock): Lock to handle thread-safe access to the frame.
        running (bool): Flag to indicate if the capture loop is running.
    """
    def __init__(self):
        self.frame = None
        self.pipeline = Gst.parse_launch(
            'v4l2src ! video/x-raw,format=YUY2,width=640,height=480 ! jpegenc ! multifilesink location=/tmp/frame.jpg'
        )
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self.on_message)
        self.lock = threading.Lock()
        self.running = False

    def start(self):
        """
        Start the GStreamer pipeline and the capture loop in a separate thread.
        """
        self.running = True
        self.pipeline.set_state(Gst.State.PLAYING)
        threading.Thread(target=self.capture_loop).start()

    def stop(self):
        """
        Stop the GStreamer pipeline and the capture loop.
        """
        self.running = False
        self.pipeline.set_state(Gst.State.NULL)

    def capture_loop(self):
        """
        Capture loop to continuously update the latest frame while the pipeline is running.
        """
        while self.running:
            with self.lock:
                self.pipeline.get_state(Gst.CLOCK_TIME_NONE)
            self.bus.poll(Gst.MessageType.EOS, Gst.CLOCK_TIME_NONE)
            self.update_frame()

    def update_frame(self):
        """
        Update the latest frame by reading the captured image from the file.
        """
        try:
            with open("/tmp/frame.jpg", "rb") as image_file:
                self.frame = image_file.read()
        except Exception as e:
            logger.error(f"Failed to read frame: {e}")

    def get_frame(self):
        """
        Get the latest captured frame in bytes.

        Returns:
            bytes: The latest captured frame.
        """
        with self.lock:
            return self.frame

    def on_message(self, bus, message):
        """
        Handle GStreamer bus messages.

        Args:
            bus (Gst.Bus): The GStreamer bus.
            message (Gst.Message): The GStreamer message.
        """
        if message.type == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            logger.error(f"GStreamer error: {err}, {debug}")
            self.stop()


class RequestHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for the image capture service.

    This handler processes GET requests to the /capture endpoint. If the request path
    is /capture, it retrieves the latest frame from the GStreamerCapture instance,
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
            frame = gstreamer_capture.get_frame()
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
    gstreamer_capture = GStreamerCapture()
    gstreamer_capture.start()
    try:
        run()
    except KeyboardInterrupt:
        pass
    finally:
        gstreamer_capture.stop()

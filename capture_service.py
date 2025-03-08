from http.server import BaseHTTPRequestHandler, HTTPServer
import base64
from loguru import logger
from picamzero import Camera

class RequestHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for the image capture service.

    This handler processes GET requests to the /capture endpoint. If the request path
    is /capture, it captures an image using the Camera instance, encodes it in base64,
    and sends it back in the response. For other paths, it returns a 404 response.
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
            camera = Camera()
            image_path = "/tmp/frame.jpg"
            camera.take_photo(image_path)
            camera.close()
            try:
                with open(image_path, "rb") as image_file:
                    frame = image_file.read()
                    base64_image = base64.b64encode(frame).decode('utf-8')
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(bytes(f"data:image/jpeg;base64,{base64_image}", "utf8"))
                    logger.info("Image sent successfully")
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                logger.error(f"Failed to capture image: {e}")
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
    run()

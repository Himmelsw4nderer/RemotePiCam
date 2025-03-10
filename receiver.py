import requests
import base64
from datetime import datetime
from loguru import logger
from concurrent.futures import ThreadPoolExecutor, as_completed

def capture_image_from_pi(pi_address):
    """
    Captures an image from a remote Raspberry Pi device.

    Args:
        pi_address (str): Network address of the Raspberry Pi

    Returns:
        tuple: (pi_address, image data if successful, None if failed)
    """
    logger.debug(f"Attempting to capture image from {pi_address}")
    try:
        response = requests.get(f'http://{pi_address}:8080/capture')
        if response.status_code == 200:
            base64_image = response.text.split(",")[1]
            image_bytes = base64.b64decode(base64_image)
            logger.info(f"Image captured successfully from {pi_address}")
            return pi_address, image_bytes
        else:
            logger.error(f"Failed to capture image from {pi_address}, status code: {response.status_code}")
            return pi_address, None
    except Exception as e:
        logger.error(f"Exception occurred while capturing image from {pi_address}: {e}")
        return pi_address, None

def save_image(image_bytes, filename):
    """
    Saves image bytes to a file on disk.

    Args:
        image_bytes (bytes): Image data to save
        filename (str): Name of file to save image as
    """
    try:
        with open(filename, "wb") as image_file:
            image_file.write(image_bytes)
            logger.info(f"Image saved as {filename}")
    except Exception as e:
        logger.error(f"Exception occurred while saving image {filename}: {e}")

if __name__ == '__main__':
    pi_addresses = ['192.168.178.184', '192.168.178.152']

    with ThreadPoolExecutor(max_workers=len(pi_addresses)) as executor:
        future_to_pi = {executor.submit(capture_image_from_pi, pi): pi for pi in pi_addresses}

        for future in as_completed(future_to_pi):
            pi_address = future_to_pi[future]
            try:
                pi_address, image_bytes = future.result()
                if image_bytes:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{pi_address}_{timestamp}.jpg"
                    save_image(image_bytes, filename)
                else:
                    logger.error(f"Failed to capture or save image from {pi_address}")
            except Exception as e:
                logger.error(f"Exception occurred for {pi_address}: {e}")

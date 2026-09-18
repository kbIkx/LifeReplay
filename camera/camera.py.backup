import cv2
from picamera2 import Picamera2

from config.config import Config
from core.logger import Logger


class Camera:
    def __init__(self):
        self.logger = Logger()
        self.camera = None

    def start(self):
        if self.camera is not None:
            return

        try:
            self.camera = Picamera2()

            config = self.camera.create_video_configuration(
                main={
                    "size": (
                        Config.CAMERA_WIDTH,
                        Config.CAMERA_HEIGHT
                    ),
                    "format": "RGB888"
                }
            )

            self.camera.configure(config)
            self.camera.start()

            self.logger.info(
                "Camera started: "
                f"{Config.CAMERA_WIDTH}x"
                f"{Config.CAMERA_HEIGHT} @ "
                f"{Config.CAMERA_FPS} FPS"
            )

        except Exception as error:
            self.logger.error(
                f"Camera failed to start: {error}"
            )

            self.camera = None

            raise

    def read(self):
        if self.camera is None:
            return None

        try:
            frame = self.camera.capture_array()

            # Picamera2 gives RGB, OpenCV expects BGR.
            frame = cv2.cvtColor(
                frame,
                cv2.COLOR_RGB2BGR
            )

            return frame

        except Exception as error:
            self.logger.warning(
                f"Failed to read frame: {error}"
            )

            return None

    def stop(self):
        if self.camera is not None:
            try:
                self.camera.stop()
            finally:
                self.camera.close()
                self.camera = None

                self.logger.info(
                    "Camera stopped"
                )

    def release(self):
        self.stop()

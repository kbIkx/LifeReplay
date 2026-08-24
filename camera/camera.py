import cv2

from config.config import Config
from core.logger import Logger


class Camera:
    def __init__(self):
        self.logger = Logger()

        self.camera = None

    def start(self):
        if self.camera is not None:
            return

        self.camera = cv2.VideoCapture(
            Config.CAMERA_INDEX
        )

        self.camera.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            Config.CAMERA_WIDTH
        )

        self.camera.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            Config.CAMERA_HEIGHT
        )

        self.camera.set(
            cv2.CAP_PROP_FPS,
            Config.CAMERA_FPS
        )

        if not self.camera.isOpened():
            self.logger.error(
                "Camera failed to open"
            )

            self.camera.release()
            self.camera = None

            raise Exception(
                "Camera not found"
            )

        self.logger.info(
            "Camera started"
        )

    def read(self):
        if self.camera is None:
            return None

        success, frame = self.camera.read()

        if not success:
            self.logger.warning(
                "Failed to read frame"
            )

            return None

        return frame

    def release(self):
        if self.camera is not None:
            self.camera.release()

            self.camera = None

            self.logger.info(
                "Camera released"
            )
import time

import cv2
import numpy as np

from core.logger import Logger


class FakeCamera:
    def __init__(self):
        self.logger = Logger()

        self.running = False
        self.counter = 0

        self.width = 640
        self.height = 480
        self.fps = 30

        self.frame_interval = (
            1.0 / self.fps
        )

        self.next_frame_time = None

    def start(self):
        self.running = True
        self.counter = 0

        self.next_frame_time = (
            time.perf_counter()
        )

        self.logger.info(
            "Fake camera started"
        )

    def read(self):
        if not self.running:
            return None

        current_time = (
            time.perf_counter()
        )

        if (
            current_time
            < self.next_frame_time
        ):
            time.sleep(
                self.next_frame_time
                - current_time
            )

        current_time = (
            time.perf_counter()
        )

        self.next_frame_time = (
            current_time
            + self.frame_interval
        )

        frame = np.zeros(
            (
                self.height,
                self.width,
                3
            ),
            dtype=np.uint8
        )

        cv2.rectangle(
            frame,
            (0, 0),
            (
                self.width - 1,
                self.height - 1
            ),
            (40, 40, 40),
            2
        )

        cv2.putText(
            frame,
            "LifeReplay TEST",
            (30, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"Frame: {self.counter}",
            (30, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (255, 255, 255),
            2
        )

        elapsed = (
            self.counter
            / self.fps
        )

        x = int(
            (
                elapsed * 120
            ) % (
                self.width - 100
            )
        )

        y = (
            self.height // 2
        )

        cv2.circle(
            frame,
            (x + 50, y),
            35,
            (0, 255, 0),
            -1
        )

        self.counter += 1

        return frame

    def stop(self):
        if not self.running:
            return

        self.running = False
        self.next_frame_time = None

        self.logger.info(
            "Fake camera stopped"
        )
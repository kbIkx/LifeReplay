from collections import deque
import time

import cv2
import numpy as np

from core.logger import Logger


class ReplayBuffer:
    def __init__(self, duration=10):
        self.logger = Logger()

        self.duration = duration

        # Храним:
        # (timestamp, jpeg_bytes)
        #
        # Это сильно экономит RAM по сравнению
        # с хранением исходных numpy-кадров.
        self.buffer = deque()

    def add_frame(self, frame):
        if frame is None:
            return

        success, encoded = cv2.imencode(
            ".jpg",
            frame,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                70
            ]
        )

        if not success:
            self.logger.warning(
                "Failed to encode frame"
            )

            return

        timestamp = time.time()

        self.buffer.append(
            (
                timestamp,
                encoded.tobytes()
            )
        )

        self._cleanup(
            timestamp
        )

    def _cleanup(
        self,
        current_time=None
    ):
        if current_time is None:
            current_time = time.time()

        while self.buffer:
            oldest_timestamp = (
                self.buffer[0][0]
            )

            if (
                current_time
                - oldest_timestamp
                > self.duration
            ):
                self.buffer.popleft()
            else:
                break

    def get_recent_frames(
        self,
        seconds
    ):
        self._cleanup()

        current_time = time.time()

        result = []

        for timestamp, encoded_frame in (
            self.buffer
        ):
            if (
                current_time - timestamp
                <= seconds
            ):
                result.append(
                    encoded_frame
                )

        return result

    def get_frames(self):
        self._cleanup()

        return [
            encoded_frame
            for _, encoded_frame
            in self.buffer
        ]

    def clear(self):
        self.buffer.clear()

    def __len__(self):
        self._cleanup()

        return len(
            self.buffer
        )

    def get_duration(self):
        self._cleanup()

        if not self.buffer:
            return 0.0

        oldest_timestamp = (
            self.buffer[0][0]
        )

        newest_timestamp = (
            self.buffer[-1][0]
        )

        return (
            newest_timestamp
            - oldest_timestamp
        )
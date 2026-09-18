from collections import deque
import threading
import time

import cv2

from core.logger import Logger


class ReplayBuffer:
    """Threaded JPEG replay buffer.

    Camera frames are accepted quickly from the main/capture loop and JPEG
    encoding happens in a background worker so encoding does not stall camera
    capture.
    """

    def __init__(self, duration=10):
        self.logger = Logger()
        self.duration = duration

        # Raw frames waiting for background JPEG encoding.
        self._raw_queue = deque(maxlen=8)
        self._raw_condition = threading.Condition()

        # (capture_timestamp, jpeg_bytes)
        self.buffer = deque()
        self._buffer_lock = threading.Lock()

        self._running = True
        self._worker = threading.Thread(
            target=self._encode_worker,
            name="ReplayBufferEncoder",
            daemon=True,
        )
        self._worker.start()

    def add_frame(self, frame, timestamp=None):
        if frame is None or not self._running:
            return

        if timestamp is None:
            timestamp = time.time()

        with self._raw_condition:
            # If the encoder falls behind, discard the oldest unprocessed
            # frame instead of blocking the camera loop.
            if len(self._raw_queue) >= self._raw_queue.maxlen:
                self._raw_queue.popleft()

            self._raw_queue.append((timestamp, frame))
            self._raw_condition.notify()

    def _encode_worker(self):
        while True:
            with self._raw_condition:
                while self._running and not self._raw_queue:
                    self._raw_condition.wait(timeout=0.5)

                if not self._running and not self._raw_queue:
                    return

                timestamp, frame = self._raw_queue.popleft()

            try:
                success, encoded = cv2.imencode(
                    ".jpg",
                    frame,
                    [cv2.IMWRITE_JPEG_QUALITY, 70],
                )

                if not success:
                    self.logger.warning(
                        "Failed to encode frame"
                    )
                    continue

                with self._buffer_lock:
                    self.buffer.append(
                        (timestamp, encoded.tobytes())
                    )
                    self._cleanup_locked(time.time())

            except Exception as error:
                self.logger.warning(
                    f"Failed to process frame: {error}"
                )

    def _cleanup_locked(self, current_time):
        while self.buffer:
            oldest_timestamp = self.buffer[0][0]

            if current_time - oldest_timestamp > self.duration:
                self.buffer.popleft()
            else:
                break

    def get_recent_frames(self, seconds):
        current_time = time.time()
        cutoff = current_time - seconds

        with self._buffer_lock:
            self._cleanup_locked(current_time)

            return [
                encoded_frame
                for timestamp, encoded_frame in self.buffer
                if timestamp >= cutoff
            ]

    def get_latest_timestamp(self):
        with self._buffer_lock:
            if not self.buffer:
                return None

            return self.buffer[-1][0]

    def get_frames_between(
        self,
        start_timestamp,
        end_timestamp
    ):
        with self._buffer_lock:
            self._cleanup_locked(time.time())

            return [
                encoded_frame
                for timestamp, encoded_frame in self.buffer
                if (
                    start_timestamp
                    <= timestamp
                    <= end_timestamp
                )
            ]

    def get_frames(self):
        with self._buffer_lock:
            self._cleanup_locked(time.time())

            return [
                encoded_frame
                for _, encoded_frame in self.buffer
            ]

    def clear(self):
        with self._raw_condition:
            self._raw_queue.clear()

        with self._buffer_lock:
            self.buffer.clear()

    def __len__(self):
        with self._buffer_lock:
            self._cleanup_locked(time.time())
            return len(self.buffer)

    def get_duration(self):
        with self._buffer_lock:
            self._cleanup_locked(time.time())

            if not self.buffer:
                return 0.0

            oldest_timestamp = self.buffer[0][0]
            newest_timestamp = self.buffer[-1][0]

            return newest_timestamp - oldest_timestamp

    def close(self):
        if not self._running:
            return

        with self._raw_condition:
            self._running = False
            self._raw_condition.notify_all()

        if self._worker.is_alive():
            self._worker.join(timeout=2.0)

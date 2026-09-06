from collections import deque
import time

from core.logger import Logger


class AudioBuffer:

    def __init__(
        self,
        duration=10
    ):
        self.logger = Logger()

        self.duration = duration

        # Stores:
        # (timestamp, pcm_bytes)
        self.buffer = deque()

    def add_chunk(
        self,
        timestamp,
        pcm_data
    ):
        if pcm_data is None:
            return

        self.buffer.append(
            (
                timestamp,
                pcm_data
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

    def get_recent_chunks(
        self,
        seconds
    ):
        self._cleanup()

        current_time = time.time()

        result = []

        for (
            timestamp,
            pcm_data
        ) in self.buffer:

            if (
                current_time
                - timestamp
                <= seconds
            ):
                result.append(
                    (
                        timestamp,
                        pcm_data
                    )
                )

        return result

    def get_chunks(self):
        self._cleanup()

        return list(
            self.buffer
        )

    def clear(self):
        self.buffer.clear()

    def __len__(self):
        self._cleanup()

        return len(
            self.buffer
        )

    def get_duration(self):
        self._cleanup()

        if len(self.buffer) < 2:
            return 0.0

        return (
            self.buffer[-1][0]
            - self.buffer[0][0]
        )

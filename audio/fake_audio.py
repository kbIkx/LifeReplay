import math
import struct
import time

from audio.audio_source import AudioSource


class FakeAudioSource(AudioSource):

    def __init__(
        self,
        sample_rate=16000,
        channels=1,
        chunk_duration=0.02
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_duration = chunk_duration

        self.samples_per_chunk = int(
            sample_rate * chunk_duration
        )

        self.phase = 0.0
        self.frequency = 440.0

        self.running = False

    def start(self):
        self.running = True
        self.phase = 0.0

    def read(self):
        if not self.running:
            return None

        samples = []

        phase_step = (
            2.0
            * math.pi
            * self.frequency
            / self.sample_rate
        )

        for _ in range(
            self.samples_per_chunk
        ):
            value = int(
                12000
                * math.sin(self.phase)
            )

            samples.append(value)

            self.phase += phase_step

            if self.phase >= 2.0 * math.pi:
                self.phase -= 2.0 * math.pi

        pcm_data = struct.pack(
            "<" + "h" * len(samples),
            *samples
        )

        return (
            time.time(),
            pcm_data
        )

    def stop(self):
        self.running = False

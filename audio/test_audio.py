import os
import time

from audio.fake_audio import FakeAudioSource
from audio.audio_buffer import AudioBuffer
from audio.wav_writer import WavWriter


OUTPUT_FILE = "test_audio.wav"


source = FakeAudioSource(
    sample_rate=16000,
    channels=1,
    chunk_duration=0.02
)

buffer = AudioBuffer(
    duration=10
)

source.start()

print("AUDIO WAV TEST")

start_time = time.time()

while time.time() - start_time < 3.0:

    result = source.read()

    if result is not None:
        timestamp, pcm_data = result

        buffer.add_chunk(
            timestamp,
            pcm_data
        )

    time.sleep(0.02)

source.stop()

chunks = buffer.get_chunks()

print(
    f"Chunks: {len(chunks)}"
)

print(
    f"Duration: "
    f"{buffer.get_duration():.2f} sec"
)

success = WavWriter.write(
    OUTPUT_FILE,
    chunks,
    sample_rate=16000,
    channels=1,
    sample_width=2
)

if not success:
    raise RuntimeError(
        "Failed to create WAV"
    )

file_size = os.path.getsize(
    OUTPUT_FILE
)

print(
    f"WAV: {OUTPUT_FILE}"
)

print(
    f"Size: {file_size} bytes"
)

if file_size <= 44:
    raise RuntimeError(
        "WAV file is too small"
    )

print("AUDIO WAV TEST PASSED")

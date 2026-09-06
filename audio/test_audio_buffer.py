import time

from audio.fake_audio import FakeAudioSource
from audio.audio_buffer import AudioBuffer


BUFFER_SECONDS = 10
TEST_SECONDS = 13


source = FakeAudioSource(
    sample_rate=16000,
    channels=1,
    chunk_duration=0.02
)

buffer = AudioBuffer(
    duration=BUFFER_SECONDS
)

source.start()

print("AUDIO BUFFER TEST")
print(
    f"Recording for {TEST_SECONDS} seconds..."
)

button_timestamp = None

start_time = time.time()

while time.time() - start_time < TEST_SECONDS:

    elapsed = time.time() - start_time

    # Имитируем нажатие кнопки примерно через 10 секунд.
    if (
        button_timestamp is None
        and elapsed >= 10.0
    ):
        button_timestamp = time.time()

        print(
            f"BUTTON MARK: "
            f"{button_timestamp:.3f}"
        )

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
    f"Chunks in buffer: {len(chunks)}"
)

print(
    f"Buffer duration: "
    f"{buffer.get_duration():.2f} sec"
)


if not chunks:
    raise RuntimeError(
        "Audio buffer is empty"
    )


# Проверяем порядок timestamp.
timestamps = [
    timestamp
    for timestamp, _ in chunks
]

for previous, current in zip(
    timestamps,
    timestamps[1:]
):
    if current <= previous:
        raise RuntimeError(
            "Timestamps are not increasing"
        )


# Получаем последние 5 секунд.
recent_chunks = (
    buffer.get_recent_chunks(5)
)

print(
    f"Recent 5 sec chunks: "
    f"{len(recent_chunks)}"
)


if not recent_chunks:
    raise RuntimeError(
        "Recent audio is empty"
    )


# Проверяем, что буфер не разросся сильно
# больше заданных 10 секунд.
if buffer.get_duration() > 10.5:
    raise RuntimeError(
        "Audio buffer exceeds expected duration"
    )


print(
    "Timestamp order: OK"
)

print(
    "Buffer limit: OK"
)

print(
    "Recent audio: OK"
)

print("AUDIO BUFFER TEST PASSED")

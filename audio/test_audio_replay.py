import time

from audio.fake_audio import FakeAudioSource
from audio.audio_buffer import AudioBuffer
from audio.audio_replay import AudioReplay
from audio.wav_writer import WavWriter


BUFFER_SECONDS = 15
PRE_SECONDS = 5
POST_SECONDS = 3


source = FakeAudioSource(
    sample_rate=16000,
    channels=1,
    chunk_duration=0.02
)

buffer = AudioBuffer(
    duration=BUFFER_SECONDS
)

replay = AudioReplay(
    buffer
)

source.start()

print("AUDIO REPLAY TEST")
print("Recording before button...")

start_time = time.time()

while time.time() - start_time < 8.0:

    result = source.read()

    if result is not None:
        timestamp, pcm_data = result

        buffer.add_chunk(
            timestamp,
            pcm_data
        )

    time.sleep(0.02)


button_timestamp = time.time()

print(
    f"BUTTON: "
    f"{button_timestamp:.3f}"
)

print(
    "Collecting POST audio..."
)

post_end_time = (
    button_timestamp
    + POST_SECONDS
)

while time.time() < post_end_time:

    result = source.read()

    if result is not None:
        timestamp, pcm_data = result

        buffer.add_chunk(
            timestamp,
            pcm_data
        )

    time.sleep(0.02)

source.stop()


pre_chunks = replay.get_pre_chunks(
    button_timestamp,
    PRE_SECONDS
)

post_chunks = replay.get_post_chunks(
    button_timestamp,
    POST_SECONDS
)

all_chunks = replay.combine(
    pre_chunks,
    post_chunks
)


print(
    f"PRE chunks: "
    f"{len(pre_chunks)}"
)

print(
    f"POST chunks: "
    f"{len(post_chunks)}"
)

print(
    f"TOTAL chunks: "
    f"{len(all_chunks)}"
)


if not pre_chunks:
    raise RuntimeError(
        "PRE audio is empty"
    )

if not post_chunks:
    raise RuntimeError(
        "POST audio is empty"
    )


pre_duration = (
    pre_chunks[-1][0]
    - pre_chunks[0][0]
)

post_duration = (
    post_chunks[-1][0]
    - post_chunks[0][0]
)


print(
    f"PRE duration: "
    f"{pre_duration:.2f} sec"
)

print(
    f"POST duration: "
    f"{post_duration:.2f} sec"
)


if pre_duration < 4.5:
    raise RuntimeError(
        "PRE audio is too short"
    )

if post_duration < 2.5:
    raise RuntimeError(
        "POST audio is too short"
    )


output_file = "test_audio_replay.wav"

success = WavWriter.write(
    output_file,
    all_chunks,
    sample_rate=16000,
    channels=1,
    sample_width=2
)

if not success:
    raise RuntimeError(
        "Failed to write replay WAV"
    )


print(
    f"WAV: {output_file}"
)

print("AUDIO REPLAY TEST PASSED")

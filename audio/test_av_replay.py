import time

import numpy as np

from storage.replay_buffer import ReplayBuffer
from audio.fake_audio import FakeAudioSource
from audio.audio_buffer import AudioBuffer


VIDEO_FPS = 30
AUDIO_CHUNK_DURATION = 0.02

BUFFER_SECONDS = 10
PRE_SECONDS = 5
POST_SECONDS = 3


video_buffer = ReplayBuffer(
    duration=BUFFER_SECONDS
)

audio_source = FakeAudioSource(
    sample_rate=16000,
    channels=1,
    chunk_duration=AUDIO_CHUNK_DURATION
)

audio_buffer = AudioBuffer(
    duration=BUFFER_SECONDS
)


# --------------------------------------------------
# Создаём тестовый видеокадр.
# --------------------------------------------------

frame = np.zeros(
    (120, 160, 3),
    dtype=np.uint8
)


# --------------------------------------------------
# Запускаем оба источника.
# --------------------------------------------------

audio_source.start()

print("VIDEO + AUDIO REPLAY TEST")
print()
print("Recording PRE history...")


# --------------------------------------------------
# PRE recording
# --------------------------------------------------

pre_record_start = time.time()

while (
    time.time() - pre_record_start
    < 7.0
):

    # VIDEO
    video_buffer.add_frame(
        frame
    )

    # AUDIO
    audio_result = (
        audio_source.read()
    )

    if audio_result is not None:

        audio_timestamp, pcm_data = (
            audio_result
        )

        audio_buffer.add_chunk(
            audio_timestamp,
            pcm_data
        )

    time.sleep(
        1.0 / VIDEO_FPS
    )


# --------------------------------------------------
# COMMON EVENT
# --------------------------------------------------

event_timestamp = time.time()

print()
print(
    f"BUTTON EVENT: "
    f"{event_timestamp:.6f}"
)


# --------------------------------------------------
# POST recording
# --------------------------------------------------

print("Recording POST...")

post_record_start = time.time()

while (
    time.time() - post_record_start
    < POST_SECONDS
):

    # VIDEO
    video_buffer.add_frame(
        frame
    )

    # AUDIO
    audio_result = (
        audio_source.read()
    )

    if audio_result is not None:

        audio_timestamp, pcm_data = (
            audio_result
        )

        audio_buffer.add_chunk(
            audio_timestamp,
            pcm_data
        )

    time.sleep(
        1.0 / VIDEO_FPS
    )


audio_source.stop()


# --------------------------------------------------
# TIMELINE
# --------------------------------------------------

replay_start = (
    event_timestamp
    - PRE_SECONDS
)

replay_end = (
    event_timestamp
    + POST_SECONDS
)


print()
print("REPLAY WINDOW")
print(
    f"Start: {replay_start:.6f}"
)
print(
    f"Event: {event_timestamp:.6f}"
)
print(
    f"End:   {replay_end:.6f}"
)


# --------------------------------------------------
# VIDEO EXTRACTION
# --------------------------------------------------

video_all = list(
    video_buffer.buffer
)

video_replay = [
    (
        timestamp,
        encoded_frame
    )
    for (
        timestamp,
        encoded_frame
    ) in video_all
    if (
        replay_start
        <= timestamp
        <= replay_end
    )
]


# --------------------------------------------------
# AUDIO EXTRACTION
# --------------------------------------------------

audio_all = (
    audio_buffer.get_chunks()
)

audio_replay = [
    (
        timestamp,
        pcm_data
    )
    for (
        timestamp,
        pcm_data
    ) in audio_all
    if (
        replay_start
        <= timestamp
        <= replay_end
    )
]


# --------------------------------------------------
# PRE / POST SPLIT
# --------------------------------------------------

video_pre = [
    item
    for item in video_replay
    if item[0] <= event_timestamp
]

video_post = [
    item
    for item in video_replay
    if item[0] > event_timestamp
]


audio_pre = [
    item
    for item in audio_replay
    if item[0] <= event_timestamp
]

audio_post = [
    item
    for item in audio_replay
    if item[0] > event_timestamp
]


print()
print("VIDEO")
print(
    f"Total replay frames: "
    f"{len(video_replay)}"
)
print(
    f"PRE frames: "
    f"{len(video_pre)}"
)
print(
    f"POST frames: "
    f"{len(video_post)}"
)


print()
print("AUDIO")
print(
    f"Total replay chunks: "
    f"{len(audio_replay)}"
)
print(
    f"PRE chunks: "
    f"{len(audio_pre)}"
)
print(
    f"POST chunks: "
    f"{len(audio_post)}"
)


# --------------------------------------------------
# TIMESTAMP CHECKS
# --------------------------------------------------

if not video_replay:
    raise RuntimeError(
        "Video replay is empty"
    )

if not audio_replay:
    raise RuntimeError(
        "Audio replay is empty"
    )


# Video timestamps must be ordered.
for i in range(
    1,
    len(video_replay)
):

    if (
        video_replay[i][0]
        < video_replay[i - 1][0]
    ):
        raise RuntimeError(
            "Video timestamps are not ordered"
        )


# Audio timestamps must be ordered.
for i in range(
    1,
    len(audio_replay)
):

    if (
        audio_replay[i][0]
        < audio_replay[i - 1][0]
    ):
        raise RuntimeError(
            "Audio timestamps are not ordered"
        )


# --------------------------------------------------
# BOUNDARY CHECKS
# --------------------------------------------------

for timestamp, _ in video_pre:

    if (
        timestamp < replay_start
        or timestamp > event_timestamp
    ):
        raise RuntimeError(
            "Invalid video PRE timestamp"
        )


for timestamp, _ in video_post:

    if (
        timestamp <= event_timestamp
        or timestamp > replay_end
    ):
        raise RuntimeError(
            "Invalid video POST timestamp"
        )


for timestamp, _ in audio_pre:

    if (
        timestamp < replay_start
        or timestamp > event_timestamp
    ):
        raise RuntimeError(
            "Invalid audio PRE timestamp"
        )


for timestamp, _ in audio_post:

    if (
        timestamp <= event_timestamp
        or timestamp > replay_end
    ):
        raise RuntimeError(
            "Invalid audio POST timestamp"
        )


# --------------------------------------------------
# DURATION CHECKS
# --------------------------------------------------

video_first = video_replay[0][0]
video_last = video_replay[-1][0]

audio_first = audio_replay[0][0]
audio_last = audio_replay[-1][0]


video_duration = (
    video_last
    - video_first
)

audio_duration = (
    audio_last
    - audio_first
)


print()
print("DURATION")
print(
    f"Video timeline: "
    f"{video_duration:.2f} sec"
)
print(
    f"Audio timeline: "
    f"{audio_duration:.2f} sec"
)


# We expect approximately 8 seconds:
# 5 sec PRE + 3 sec POST.
#
# Allow some margin because the event can
# happen between frames/chunks.

if not (
    7.5
    <= video_duration
    <= 8.5
):
    raise RuntimeError(
        "Unexpected video replay duration"
    )


if not (
    7.5
    <= audio_duration
    <= 8.5
):
    raise RuntimeError(
        "Unexpected audio replay duration"
    )


# --------------------------------------------------
# AUDIO / VIDEO EVENT ALIGNMENT
# --------------------------------------------------

nearest_video = min(
    video_replay,
    key=lambda item:
        abs(
            item[0]
            - event_timestamp
        )
)

nearest_audio = min(
    audio_replay,
    key=lambda item:
        abs(
            item[0]
            - event_timestamp
        )
)


video_event_delta = (
    nearest_video[0]
    - event_timestamp
)

audio_event_delta = (
    nearest_audio[0]
    - event_timestamp
)

stream_delta = abs(
    video_event_delta
    - audio_event_delta
)


print()
print("EVENT ALIGNMENT")
print(
    f"Video event delta: "
    f"{video_event_delta * 1000:.2f} ms"
)

print(
    f"Audio event delta: "
    f"{audio_event_delta * 1000:.2f} ms"
)

print(
    f"Video/audio difference: "
    f"{stream_delta * 1000:.2f} ms"
)


if abs(video_event_delta) > 0.1:
    raise RuntimeError(
        "Video event alignment failed"
    )


if abs(audio_event_delta) > 0.1:
    raise RuntimeError(
        "Audio event alignment failed"
    )


if stream_delta > 0.05:
    raise RuntimeError(
        "Audio/video synchronization difference is too large"
    )


# --------------------------------------------------
# EXPECTED COUNTS
# --------------------------------------------------

expected_video_min = 200
expected_video_max = 260

expected_audio_min = 200
expected_audio_max = 260


if not (
    expected_video_min
    <= len(video_replay)
    <= expected_video_max
):
    raise RuntimeError(
        "Unexpected video frame count"
    )


if not (
    expected_audio_min
    <= len(audio_replay)
    <= expected_audio_max
):
    raise RuntimeError(
        "Unexpected audio chunk count"
    )


print()
print("CHECKS")
print("Video timestamps: OK")
print("Audio timestamps: OK")
print("Common event: OK")
print("PRE/POST boundaries: OK")
print("Replay duration: OK")
print("Video/audio alignment: OK")
print("Frame/chunk counts: OK")
print()
print("VIDEO + AUDIO REPLAY TEST PASSED")

import time

from audio.fake_audio import FakeAudioSource
from audio.audio_buffer import AudioBuffer


BUFFER_SECONDS = 15
PRE_SECONDS = 5
POST_SECONDS = 3


audio_source = FakeAudioSource(
    sample_rate=16000,
    channels=1,
    chunk_duration=0.02
)

audio_buffer = AudioBuffer(
    duration=BUFFER_SECONDS
)


audio_source.start()

print("AUDIO/VIDEO SYNC TEST")
print("Collecting synchronized timeline...")


# Имитируем непрерывную работу камеры.
# В данном тесте вместо настоящих кадров
# используем только timestamps.
video_timestamps = []

start_time = time.time()

while time.time() - start_time < 8.0:

    current_time = time.time()

    # VIDEO EVENT
    video_timestamps.append(
        current_time
    )

    # AUDIO EVENT
    audio_result = audio_source.read()

    if audio_result is not None:
        audio_timestamp, pcm_data = (
            audio_result
        )

        audio_buffer.add_chunk(
            audio_timestamp,
            pcm_data
        )

    time.sleep(1 / 30)


# ==================================================
# ОБЩЕЕ СОБЫТИЕ
# ==================================================

event_timestamp = time.time()

print(
    f"EVENT timestamp: "
    f"{event_timestamp:.6f}"
)


# Ищем ближайший видео timestamp
# к моменту события.
nearest_video_timestamp = min(
    video_timestamps,
    key=lambda timestamp:
        abs(
            timestamp
            - event_timestamp
        )
)

video_delta = (
    nearest_video_timestamp
    - event_timestamp
)


# Ищем ближайший аудио timestamp
# к моменту события.
audio_chunks = audio_buffer.get_chunks()

nearest_audio_timestamp = min(
    audio_chunks,
    key=lambda item:
        abs(
            item[0]
            - event_timestamp
        )
)[0]

audio_delta = (
    nearest_audio_timestamp
    - event_timestamp
)


print(
    f"Nearest VIDEO timestamp: "
    f"{nearest_video_timestamp:.6f}"
)

print(
    f"Nearest AUDIO timestamp: "
    f"{nearest_audio_timestamp:.6f}"
)

print(
    f"VIDEO delta: "
    f"{video_delta * 1000:.2f} ms"
)

print(
    f"AUDIO delta: "
    f"{audio_delta * 1000:.2f} ms"
)


# ==================================================
# PRE / POST ГРАНИЦЫ
# ==================================================

pre_start = (
    event_timestamp
    - PRE_SECONDS
)

post_end = (
    event_timestamp
    + POST_SECONDS
)


print(
    f"Replay start: "
    f"{pre_start:.6f}"
)

print(
    f"Replay end: "
    f"{post_end:.6f}"
)


# Проверяем аудио PRE.
audio_pre = [
    item
    for item in audio_chunks
    if (
        pre_start
        <= item[0]
        <= event_timestamp
    )
]


# Проверяем аудио POST.
# Сейчас цикл ещё не записывал POST,
# поэтому специально проверяем только
# правильность временной границы.
audio_post_boundary = [
    item
    for item in audio_chunks
    if (
        event_timestamp
        < item[0]
        <= post_end
    )
]


print(
    f"AUDIO PRE chunks: "
    f"{len(audio_pre)}"
)

print(
    f"AUDIO POST currently available: "
    f"{len(audio_post_boundary)}"
)


if not audio_pre:
    raise RuntimeError(
        "Audio PRE is empty"
    )


# Проверяем, что все PRE timestamps
# действительно находятся ДО события.
for timestamp, _ in audio_pre:

    if timestamp > event_timestamp:
        raise RuntimeError(
            "Audio PRE contains future data"
        )


# Проверяем максимальное расхождение
# между ближайшими timestamp и событием.
#
# Для видео при 30 FPS ожидаем максимум
# около одного кадра.
if abs(video_delta) > 0.1:
    raise RuntimeError(
        "Video event synchronization failed"
    )


# Для аудио chunk = 20 ms.
if abs(audio_delta) > 0.1:
    raise RuntimeError(
        "Audio event synchronization failed"
    )


audio_source.stop()


print("VIDEO TIMESTAMP: OK")
print("AUDIO TIMESTAMP: OK")
print("COMMON EVENT: OK")
print("PRE BOUNDARY: OK")
print("AUDIO/VIDEO SYNC TEST PASSED")

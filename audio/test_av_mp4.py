import math
import struct
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np

from config.config import Config
from storage.replay_manager import ReplayManager


TEST_DURATION = 3.0
FPS = 30
SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2
MAX_SYNC_ERROR = 0.1


def make_frame(index):
    frame = np.zeros(
        (480, 640, 3),
        dtype=np.uint8
    )

    cv2.putText(
        frame,
        f"LifeReplay A/V TEST {index}",
        (80, 240),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (255, 255, 255),
        2
    )

    success, encoded = cv2.imencode(
        ".jpg",
        frame
    )

    if not success:
        raise RuntimeError(
            "Failed to encode test frame"
        )

    return encoded.tobytes()


def make_audio_chunk(
    chunk_index,
    samples_per_chunk
):
    frequency = 440.0
    samples = []

    start_sample = (
        chunk_index
        * samples_per_chunk
    )

    for i in range(samples_per_chunk):
        sample_index = (
            start_sample + i
        )

        value = int(
            12000
            * math.sin(
                2.0
                * math.pi
                * frequency
                * sample_index
                / SAMPLE_RATE
            )
        )

        samples.append(value)

    return struct.pack(
        "<" + "h" * len(samples),
        *samples
    )


def probe(file_path):
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels,duration",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(file_path)
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True
    )

    import json

    return json.loads(result.stdout)


def main():
    print("A/V MP4 AUTOMATED TEST")
    print()

    manager = ReplayManager()

    frame_count = int(
        TEST_DURATION * FPS
    )

    samples_per_chunk = int(
        SAMPLE_RATE / FPS
    )

    pre_frame_count = int(
        frame_count * 2 / 3
    )

    post_frame_count = (
        frame_count - pre_frame_count
    )

    pre_frames = []
    post_frames = []

    pre_audio_chunks = []
    post_audio_chunks = []

    base_timestamp = time.time()

    for i in range(frame_count):
        frame = make_frame(i)

        timestamp = (
            base_timestamp
            + i / FPS
        )

        audio = make_audio_chunk(
            i,
            samples_per_chunk
        )

        if i < pre_frame_count:
            pre_frames.append(frame)
            pre_audio_chunks.append(
                (
                    timestamp,
                    audio
                )
            )
        else:
            post_frames.append(frame)
            post_audio_chunks.append(
                (
                    timestamp,
                    audio
                )
            )

    print(
        f"Video frames: "
        f"{len(pre_frames) + len(post_frames)}"
    )

    print(
        f"Audio chunks: "
        f"{len(pre_audio_chunks) + len(post_audio_chunks)}"
    )

    print(
        f"Expected duration: "
        f"{TEST_DURATION:.2f} sec"
    )

    replay = manager.save_encoded_av_replay(
        pre_frames,
        post_frames,
        pre_audio_chunks,
        post_audio_chunks,
        pre_frame_count / FPS,
        post_frame_count / FPS
    )

    if replay is None:
        raise RuntimeError(
            "ReplayManager failed to create A/V replay"
        )

    file_path = Path(
        replay.file_path
    )

    if not file_path.exists():
        raise RuntimeError(
            f"Replay file does not exist: {file_path}"
        )

    print()
    print(
        f"Created: {file_path}"
    )

    data = probe(file_path)

    streams = data.get(
        "streams",
        []
    )

    video = next(
        (
            stream
            for stream in streams
            if stream.get("codec_type") == "video"
        ),
        None
    )

    audio = next(
        (
            stream
            for stream in streams
            if stream.get("codec_type") == "audio"
        ),
        None
    )

    if video is None:
        raise RuntimeError(
            "VIDEO STREAM NOT FOUND"
        )

    if audio is None:
        raise RuntimeError(
            "AUDIO STREAM NOT FOUND"
        )

    if video.get("codec_name") != "h264":
        raise RuntimeError(
            f"Expected H.264, got {video.get('codec_name')}"
        )

    if audio.get("codec_name") != "aac":
        raise RuntimeError(
            f"Expected AAC, got {audio.get('codec_name')}"
        )

    if video.get("width") != 640:
        raise RuntimeError(
            f"Expected width 640, got {video.get('width')}"
        )

    if video.get("height") != 480:
        raise RuntimeError(
            f"Expected height 480, got {video.get('height')}"
        )

    if video.get("r_frame_rate") != "30/1":
        raise RuntimeError(
            f"Expected 30 FPS, got {video.get('r_frame_rate')}"
        )

    if int(audio.get("sample_rate", 0)) != SAMPLE_RATE:
        raise RuntimeError(
            f"Expected 16000 Hz, got {audio.get('sample_rate')}"
        )

    if int(audio.get("channels", 0)) != CHANNELS:
        raise RuntimeError(
            f"Expected mono, got {audio.get('channels')} channels"
        )

    video_duration = float(
        video.get("duration", 0)
    )

    audio_duration = float(
        audio.get("duration", 0)
    )

    format_duration = float(
        data.get("format", {}).get(
            "duration",
            0
        )
    )

    sync_error = abs(
        video_duration
        - audio_duration
    )

    print()
    print("STREAM CHECK")
    print(
        f"Video: H.264 "
        f"{video_duration:.3f} sec"
    )
    print(
        f"Audio: AAC "
        f"{audio_duration:.3f} sec"
    )
    print(
        f"Format duration: "
        f"{format_duration:.3f} sec"
    )
    print(
        f"A/V duration difference: "
        f"{sync_error * 1000:.1f} ms"
    )

    if video_duration <= 0:
        raise RuntimeError(
            "Invalid video duration"
        )

    if audio_duration <= 0:
        raise RuntimeError(
            "Invalid audio duration"
        )

    if sync_error > MAX_SYNC_ERROR:
        raise RuntimeError(
            f"A/V sync error too large: "
            f"{sync_error * 1000:.1f} ms"
        )

    print()
    print("CHECKS")
    print("Video stream: OK")
    print("Audio stream: OK")
    print("H.264 codec: OK")
    print("AAC codec: OK")
    print("640x480: OK")
    print("30 FPS: OK")
    print("16 kHz mono: OK")
    print("A/V duration: OK")
    print("A/V synchronization: OK")
    print()
    print("A/V MP4 TEST PASSED")

    try:
        file_path.unlink()
    except OSError:
        pass

    metadata_path = (
        Path(Config.REPLAY_PATH)
        / "metadata"
        / f"{replay.replay_id}.json"
    )

    try:
        metadata_path.unlink()
    except OSError:
        pass


if __name__ == "__main__":
    main()

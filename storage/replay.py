from dataclasses import dataclass


@dataclass
class Replay:

    replay_id: str
    created_at: float

    pre_seconds: int
    post_seconds: int

    frame_count: int
    duration_seconds: float

    file_path: str

    file_size_bytes: int = 0

    width: int = 0
    height: int = 0
    fps: float = 0.0

    audio: bool = False
    audio_sample_rate: int = 0
    audio_channels: int = 0

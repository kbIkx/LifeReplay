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
import json
from pathlib import Path


class Settings:
    FILE_PATH = (
        Path(__file__).resolve().parent
        / "settings.json"
    )

    DEFAULTS = {
        "camera_width": 640,
        "camera_height": 480,
        "camera_fps": 30,

        "buffer_seconds": 40,
        "pre_seconds": 10,
        "post_seconds": 5,

        "replay_buffer_enabled": True,

        "auto_delete": False,
        "storage_limit_mb": 1024,
    }

    @classmethod
    def load(cls):
        if not cls.FILE_PATH.exists():
            cls.save(cls.DEFAULTS.copy())

        try:
            with open(
                cls.FILE_PATH,
                "r",
                encoding="utf-8"
            ) as file:
                data = json.load(file)

        except Exception:
            data = cls.DEFAULTS.copy()
            cls.save(data)

        result = cls.DEFAULTS.copy()
        result.update(data)

        return result

    @classmethod
    def save(cls, settings):
        cls.FILE_PATH.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            cls.FILE_PATH,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                settings,
                file,
                indent=4,
                ensure_ascii=False
            )

    @classmethod
    def update(cls, changes):
        settings = cls.load()

        settings.update(changes)

        cls.validate(settings)

        cls.save(settings)

        return settings

    @classmethod
    def validate(cls, settings):
        width = int(settings["camera_width"])
        height = int(settings["camera_height"])
        fps = int(settings["camera_fps"])

        buffer_seconds = int(settings["buffer_seconds"])
        pre_seconds = int(settings["pre_seconds"])
        post_seconds = int(settings["post_seconds"])
        storage_limit_mb = int(settings["storage_limit_mb"])

        valid_resolutions = {
            (640, 480),
            (1296, 972),
            (1920, 1080),
            (2592, 1944),
        }

        if (width, height) not in valid_resolutions:
            raise ValueError(
                "Unsupported camera resolution"
            )

        if fps < 1 or fps > 60:
            raise ValueError(
                "FPS must be between 1 and 60"
            )

        if buffer_seconds < 40:
            raise ValueError(
                "Buffer duration must be at least 40 seconds"
            )

        if pre_seconds < 0:
            raise ValueError(
                "PRE seconds cannot be negative"
            )

        if pre_seconds > 40:
            raise ValueError(
                "PRE seconds cannot exceed 40 seconds"
            )

        if pre_seconds > buffer_seconds:
            raise ValueError(
                "PRE seconds cannot exceed buffer duration"
            )

        if post_seconds < 0:
            raise ValueError(
                "POST seconds cannot be negative"
            )

        if post_seconds > 20:
            raise ValueError(
                "POST seconds cannot exceed 20 seconds"
            )

        if storage_limit_mb < 100:
            raise ValueError(
                "Storage limit must be at least 100 MB"
            )

        settings["replay_buffer_enabled"] = bool(
            settings["replay_buffer_enabled"]
        )

        settings["auto_delete"] = bool(
            settings["auto_delete"]
        )

        settings["camera_width"] = width
        settings["camera_height"] = height
        settings["camera_fps"] = fps

        settings["buffer_seconds"] = buffer_seconds
        settings["pre_seconds"] = pre_seconds
        settings["post_seconds"] = post_seconds

        settings["storage_limit_mb"] = storage_limit_mb


def load_settings():
    return Settings.load()

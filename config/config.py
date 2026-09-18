from config.settings import load_settings


class Config:
    # Camera
    CAMERA_INDEX = 0
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    CAMERA_FPS = 30

    # Replay
    BUFFER_SECONDS = 10
    PRE_SECONDS = 10
    POST_SECONDS = 5

    # Storage
    REPLAY_PATH = "replays"

    # Logging
    LOG_PATH = "logs/lifereplay.log"

    # GPIO
    GPIO_ENABLED = True

    GPIO_BUTTON_PIN = 17

    GPIO_GREEN_PIN = 27
    GPIO_YELLOW_PIN = 22
    GPIO_RED_PIN = 24

    GPIO_BUZZER_PIN = 23

    @classmethod
    def reload(cls):
        settings = load_settings()

        cls.CAMERA_WIDTH = settings[
            "camera_width"
        ]

        cls.CAMERA_HEIGHT = settings[
            "camera_height"
        ]

        cls.CAMERA_FPS = settings[
            "camera_fps"
        ]

        cls.BUFFER_SECONDS = settings[
            "buffer_seconds"
        ]

        cls.PRE_SECONDS = settings[
            "pre_seconds"
        ]

        cls.POST_SECONDS = settings[
            "post_seconds"
        ]

        return settings


Config.reload()

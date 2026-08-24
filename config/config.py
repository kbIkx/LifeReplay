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

    # Reserved for future buzzer / physical signal
    GPIO_BUZZER_PIN = 23
import time

from picamera2 import Picamera2


WIDTH = 1296
HEIGHT = 972
SECONDS = 10


camera = Picamera2()

config = camera.create_video_configuration(
    main={
        "size": (WIDTH, HEIGHT),
        "format": "RGB888"
    },
    controls={
        "FrameRate": 30
    }
)

camera.configure(config)
camera.start()

print(f"Camera started: {WIDTH}x{HEIGHT}")
print(f"Testing for {SECONDS} seconds...")

start = time.monotonic()
frames = 0

try:
    while time.monotonic() - start < SECONDS:
        camera.capture_array()
        frames += 1

finally:
    camera.stop()
    camera.close()

elapsed = time.monotonic() - start

print()
print(f"Frames: {frames}")
print(f"Time:   {elapsed:.2f}s")
print(f"FPS:    {frames / elapsed:.2f}")

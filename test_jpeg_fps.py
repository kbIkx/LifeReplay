import time

import cv2
from picamera2 import Picamera2


WIDTH = 1296
HEIGHT = 972
FPS = 30
SECONDS = 10


camera = Picamera2()

config = camera.create_video_configuration(
    main={
        "size": (WIDTH, HEIGHT),
        "format": "RGB888"
    },
    controls={
        "FrameRate": FPS
    }
)

camera.configure(config)
camera.start()

print(f"Camera started: {WIDTH}x{HEIGHT}")
print("Testing RGB -> BGR -> JPEG...")
print(f"Duration: {SECONDS} seconds")

start = time.monotonic()
frames = 0
total_encode_time = 0.0

try:
    while time.monotonic() - start < SECONDS:
        frame = camera.capture_array()

        encode_start = time.monotonic()

        frame = cv2.cvtColor(
            frame,
            cv2.COLOR_RGB2BGR
        )

        success, encoded = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 70]
        )

        total_encode_time += (
            time.monotonic() - encode_start
        )

        if success:
            frames += 1

finally:
    camera.stop()
    camera.close()

elapsed = time.monotonic() - start

print()
print(f"Frames:              {frames}")
print(f"Time:                {elapsed:.2f}s")
print(f"FPS:                 {frames / elapsed:.2f}")
print(f"Avg JPEG/frame:      {total_encode_time / frames * 1000:.2f} ms")
print(f"JPEG throughput:     {frames / total_encode_time:.2f} FPS")

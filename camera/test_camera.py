import cv2
from camera import Camera


cam = Camera()

while True:
    frame = cam.read()

    if frame is None:
        break

    cv2.imshow("LifeReplay Camera Test", frame)

    if cv2.waitKey(1) == ord("q"):
        break


cam.release()
cv2.destroyAllWindows()


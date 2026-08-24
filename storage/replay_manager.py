import os
import time
import uuid

import cv2
import numpy as np

from config.config import Config
from core.logger import Logger
from storage.replay import Replay


class ReplayManager:
    def __init__(self):
        self.logger = Logger()

        self.replay_path = (
            Config.REPLAY_PATH
        )

        os.makedirs(
            self.replay_path,
            exist_ok=True
        )

    def _decode_frame(
        self,
        encoded_frame
    ):
        if encoded_frame is None:
            return None

        try:
            array = np.frombuffer(
                encoded_frame,
                dtype=np.uint8
            )

            frame = cv2.imdecode(
                array,
                cv2.IMREAD_COLOR
            )

            return frame

        except Exception as error:
            self.logger.error(
                f"Failed to decode frame: "
                f"{error}"
            )

            return None

    def save_encoded_replay(
        self,
        pre_frames,
        post_frames,
        pre_seconds,
        post_seconds
    ):
        if not pre_frames and not post_frames:
            self.logger.warning(
                "Cannot save empty replay"
            )

            return None

        replay_id = (
            uuid.uuid4().hex[:12]
        )

        created_at = time.time()

        expected_frame_count = (
            len(pre_frames)
            + len(post_frames)
        )

        filename = (
            f"replay_{replay_id}.avi"
        )

        file_path = os.path.join(
            self.replay_path,
            filename
        )

        first_encoded_frame = None

        if pre_frames:
            first_encoded_frame = (
                pre_frames[0]
            )
        elif post_frames:
            first_encoded_frame = (
                post_frames[0]
            )

        first_frame = (
            self._decode_frame(
                first_encoded_frame
            )
        )

        if first_frame is None:
            self.logger.error(
                "Failed to decode first replay frame"
            )

            return None

        height, width = (
            first_frame.shape[:2]
        )

        fps = Config.CAMERA_FPS

        fourcc = (
            cv2.VideoWriter_fourcc(
                *"MJPG"
            )
        )

        writer = cv2.VideoWriter(
            file_path,
            fourcc,
            fps,
            (width, height)
        )

        if not writer.isOpened():
            self.logger.error(
                "Failed to open video writer"
            )

            return None

        written_frame_count = 0
        failed_frame_count = 0

        try:
            for encoded_frame in (
                pre_frames
            ):
                frame = (
                    self._decode_frame(
                        encoded_frame
                    )
                )

                if frame is None:
                    failed_frame_count += 1
                    continue

                writer.write(
                    frame
                )

                written_frame_count += 1

            for encoded_frame in (
                post_frames
            ):
                frame = (
                    self._decode_frame(
                        encoded_frame
                    )
                )

                if frame is None:
                    failed_frame_count += 1
                    continue

                writer.write(
                    frame
                )

                written_frame_count += 1

        finally:
            writer.release()

        replay = Replay(
            replay_id=replay_id,
            created_at=created_at,
            pre_seconds=pre_seconds,
            post_seconds=post_seconds,
            frame_count=written_frame_count,
            duration_seconds=(
                written_frame_count
                / fps
            ),
            file_path=file_path
        )

        self.logger.info(
            f"Replay saved: {file_path}"
        )

        self.logger.info(
            f"Replay frames: "
            f"expected={expected_frame_count}, "
            f"written={written_frame_count}, "
            f"failed={failed_frame_count}"
        )

        return replay

    def save_replay(
        self,
        frames,
        pre_seconds,
        post_seconds
    ):
        if not frames:
            self.logger.warning(
                "Cannot save empty replay"
            )

            return None

        encoded_frames = []

        for frame in frames:
            if frame is None:
                continue

            success, encoded = (
                cv2.imencode(
                    ".jpg",
                    frame,
                    [
                        cv2.IMWRITE_JPEG_QUALITY,
                        70
                    ]
                )
            )

            if not success:
                continue

            encoded_frames.append(
                encoded.tobytes()
            )

        return self.save_encoded_replay(
            encoded_frames,
            [],
            pre_seconds,
            post_seconds
        )

    def list_replays(self):
        replays = []

        if not os.path.exists(
            self.replay_path
        ):
            return replays

        for filename in sorted(
            os.listdir(
                self.replay_path
            )
        ):
            if not filename.startswith(
                "replay_"
            ):
                continue

            if not filename.endswith(
                ".avi"
            ):
                continue

            file_path = os.path.join(
                self.replay_path,
                filename
            )

            if not os.path.isfile(
                file_path
            ):
                continue

            replay_id = filename[
                7:-4
            ]

            created_at = (
                os.path.getmtime(
                    file_path
                )
            )

            frame_count = 0

            capture = cv2.VideoCapture(
                file_path
            )

            if capture.isOpened():
                while True:
                    success, _ = (
                        capture.read()
                    )

                    if not success:
                        break

                    frame_count += 1

            capture.release()

            replay = Replay(
                replay_id=replay_id,
                created_at=created_at,
                pre_seconds=Config.PRE_SECONDS,
                post_seconds=Config.POST_SECONDS,
                frame_count=frame_count,
                duration_seconds=(
                    frame_count
                    / Config.CAMERA_FPS
                ),
                file_path=file_path
            )

            replays.append(
                replay
            )

        return replays

    def load_replay(
        self,
        replay_id
    ):
        filename = (
            f"replay_{replay_id}.avi"
        )

        file_path = os.path.join(
            self.replay_path,
            filename
        )

        if not os.path.isfile(
            file_path
        ):
            self.logger.warning(
                f"Replay not found: "
                f"{replay_id}"
            )

            return None

        capture = cv2.VideoCapture(
            file_path
        )

        if not capture.isOpened():
            self.logger.error(
                f"Failed to open replay: "
                f"{replay_id}"
            )

            return None

        frames = []

        try:
            while True:
                success, frame = (
                    capture.read()
                )

                if not success:
                    break

                frames.append(
                    frame
                )

        finally:
            capture.release()

        self.logger.info(
            f"Replay loaded: "
            f"{replay_id}"
        )

        return frames

    def delete_replay(
        self,
        replay_id
    ):
        filename = (
            f"replay_{replay_id}.avi"
        )

        file_path = os.path.join(
            self.replay_path,
            filename
        )

        if not os.path.isfile(
            file_path
        ):
            self.logger.warning(
                f"Replay not found: "
                f"{replay_id}"
            )

            return False

        try:
            os.remove(
                file_path
            )

        except OSError as error:
            self.logger.error(
                f"Failed to delete replay: "
                f"{error}"
            )

            return False

        self.logger.info(
            f"Replay deleted: "
            f"{replay_id}"
        )

        return True
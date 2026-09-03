import os
import time
import uuid
import subprocess

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

        self.ffmpeg_path = (
            "/usr/bin/ffmpeg"
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

    def _write_mp4(
        self,
        file_path,
        pre_frames,
        post_frames,
        width,
        height,
        fps
    ):
        command = [
            self.ffmpeg_path,

            "-y",

            "-f",
            "rawvideo",

            "-vcodec",
            "rawvideo",

            "-pix_fmt",
            "bgr24",

            "-s",
            f"{width}x{height}",

            "-r",
            str(fps),

            "-i",
            "-",

            "-an",

            "-c:v",
            "libx264",

            "-preset",
            "veryfast",

            "-crf",
            "23",

            "-pix_fmt",
            "yuv420p",

            "-movflags",
            "+faststart",

            file_path
        ]

        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )

        except Exception as error:
            self.logger.error(
                f"Failed to start FFmpeg: "
                f"{error}"
            )

            return 0, len(pre_frames) + len(post_frames)

        written_frame_count = 0
        failed_frame_count = 0

        try:
            all_frames = (
                list(pre_frames)
                + list(post_frames)
            )

            for encoded_frame in all_frames:
                frame = self._decode_frame(
                    encoded_frame
                )

                if frame is None:
                    failed_frame_count += 1
                    continue

                if (
                    frame.shape[1] != width
                    or frame.shape[0] != height
                ):
                    self.logger.warning(
                        "Skipping frame with "
                        "unexpected resolution"
                    )

                    failed_frame_count += 1
                    continue

                try:
                    process.stdin.write(
                        frame.tobytes()
                    )

                    written_frame_count += 1

                except (
                    BrokenPipeError,
                    OSError
                ):
                    failed_frame_count += 1

                    self.logger.error(
                        "FFmpeg pipe closed "
                        "unexpectedly"
                    )

                    break

        finally:
            if process.stdin is not None:
                try:
                    process.stdin.close()
                except OSError:
                    pass

        stderr_output = (
            process.stderr.read()
            if process.stderr is not None
            else b""
        )

        return_code = (
            process.wait()
        )

        if return_code != 0:
            error_text = (
                stderr_output
                .decode(
                    "utf-8",
                    errors="replace"
                )
            )

            self.logger.error(
                f"FFmpeg failed with "
                f"exit code {return_code}"
            )

            self.logger.error(
                f"FFmpeg output: "
                f"{error_text[-4000:]}"
            )

            if os.path.isfile(
                file_path
            ):
                try:
                    os.remove(
                        file_path
                    )
                except OSError:
                    pass

            return (
                0,
                len(pre_frames) + len(post_frames)
            )

        return (
            written_frame_count,
            failed_frame_count
        )

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
            f"replay_{replay_id}.mp4"
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
                "Failed to decode first "
                "replay frame"
            )

            return None

        height, width = (
            first_frame.shape[:2]
        )

        fps = Config.CAMERA_FPS

        if fps <= 0:
            self.logger.error(
                f"Invalid camera FPS: {fps}"
            )

            return None

        self.logger.info(
            f"Starting MP4 encoding: "
            f"{file_path}"
        )

        self.logger.info(
            f"Video parameters: "
            f"{width}x{height} @ {fps} FPS"
        )

        (
            written_frame_count,
            failed_frame_count
        ) = self._write_mp4(
            file_path=file_path,
            pre_frames=pre_frames,
            post_frames=post_frames,
            width=width,
            height=height,
            fps=fps
        )

        if written_frame_count == 0:
            self.logger.error(
                "No frames were written "
                "to MP4"
            )

            return None

        if not os.path.isfile(
            file_path
        ):
            self.logger.error(
                "MP4 file was not created"
            )

            return None

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

        self.logger.info(
            f"Replay duration: "
            f"{replay.duration_seconds:.2f} seconds"
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

    def _get_replay_files(
        self
    ):
        if not os.path.exists(
            self.replay_path
        ):
            return []

        replay_files = []

        for filename in os.listdir(
            self.replay_path
        ):
            if not filename.startswith(
                "replay_"
            ):
                continue

            if not (
                filename.endswith(".mp4")
                or filename.endswith(".avi")
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

            replay_files.append(
                filename
            )

        return sorted(
            replay_files,
            reverse=True
        )

    def list_replays(self):
        replays = []

        replay_files = (
            self._get_replay_files()
        )

        for filename in replay_files:
            if filename.endswith(
                ".mp4"
            ):
                extension_length = 4
            else:
                extension_length = 4

            replay_id = filename[
                7:-extension_length
            ]

            file_path = os.path.join(
                self.replay_path,
                filename
            )

            created_at = (
                os.path.getmtime(
                    file_path
                )
            )

            frame_count = 0
            fps = Config.CAMERA_FPS

            capture = cv2.VideoCapture(
                file_path
            )

            if capture.isOpened():
                detected_fps = (
                    capture.get(
                        cv2.CAP_PROP_FPS
                    )
                )

                if detected_fps > 0:
                    fps = detected_fps

                detected_frame_count = (
                    capture.get(
                        cv2.CAP_PROP_FRAME_COUNT
                    )
                )

                if detected_frame_count > 0:
                    frame_count = int(
                        detected_frame_count
                    )

            capture.release()

            if frame_count <= 0:
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
                    frame_count / fps
                    if fps > 0
                    else 0
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
        mp4_filename = (
            f"replay_{replay_id}.mp4"
        )

        avi_filename = (
            f"replay_{replay_id}.avi"
        )

        mp4_path = os.path.join(
            self.replay_path,
            mp4_filename
        )

        avi_path = os.path.join(
            self.replay_path,
            avi_filename
        )

        if os.path.isfile(
            mp4_path
        ):
            file_path = mp4_path

        elif os.path.isfile(
            avi_path
        ):
            file_path = avi_path

        else:
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
        mp4_filename = (
            f"replay_{replay_id}.mp4"
        )

        avi_filename = (
            f"replay_{replay_id}.avi"
        )

        mp4_path = os.path.join(
            self.replay_path,
            mp4_filename
        )

        avi_path = os.path.join(
            self.replay_path,
            avi_filename
        )

        file_path = None

        if os.path.isfile(
            mp4_path
        ):
            file_path = mp4_path

        elif os.path.isfile(
            avi_path
        ):
            file_path = avi_path

        else:
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
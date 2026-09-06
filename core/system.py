import time

import cv2

from config.config import Config
from core.logger import Logger

from storage.replay_buffer import ReplayBuffer
from storage.replay_manager import ReplayManager

from audio.fake_audio import FakeAudioSource
from audio.audio_buffer import AudioBuffer

from camera.camera import Camera
from input.button import Button
from hardware.gpio import GPIOHardware


class LifeReplaySystem:
    def __init__(self):
        self.logger = Logger()

        self.buffer = ReplayBuffer(
            Config.BUFFER_SECONDS
        )

        self.audio_source = FakeAudioSource(
            sample_rate=16000,
            channels=1,
            chunk_duration=1.0 / Config.CAMERA_FPS
        )

        self.audio_buffer = AudioBuffer(
            Config.BUFFER_SECONDS
        )

        self.replay_manager = (
            ReplayManager()
        )

        self.camera = Camera()

        self.button = Button()

        self.hardware = GPIOHardware()

        self.running = False

        self.rollback_active = False
        self.rollback_start_time = None
        self.event_timestamp = None

        self.pre_frames = []
        self.post_frames = []

        self.pre_audio_chunks = []
        self.post_audio_chunks = []

        self.logger.info(
            "LifeReplay system initialized"
        )

    def encode_frame(
        self,
        frame
    ):
        if frame is None:
            return None

        success, encoded = cv2.imencode(
            ".jpg",
            frame,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                70
            ]
        )

        if not success:
            self.logger.warning(
                "Failed to encode frame"
            )

            return None

        return encoded.tobytes()

    def process_audio(self):
        audio_result = (
            self.audio_source.read()
        )

        if audio_result is None:
            return

        timestamp, pcm_data = (
            audio_result
        )

        self.audio_buffer.add_chunk(
            timestamp,
            pcm_data
        )

        if self.rollback_active:
            self.post_audio_chunks.append(
                (
                    timestamp,
                    pcm_data
                )
            )

    def process_frame(
        self,
        frame
    ):
        self.buffer.add_frame(
            frame
        )

        if self.rollback_active:
            encoded_frame = (
                self.encode_frame(
                    frame
                )
            )

            if encoded_frame is not None:
                self.post_frames.append(
                    encoded_frame
                )

            elapsed = (
                time.time()
                - self.rollback_start_time
            )

            if (
                elapsed
                >= Config.POST_SECONDS
            ):
                self.finish_rollback()

    def start(self):
        self.running = True

        self.camera.start()
        self.button.start()
        self.audio_source.start()

        self.hardware.start()

        self.logger.info(
            "LifeReplay system started"
        )

    def update(self):
        if not self.running:
            return

        self.process_audio()

        frame = self.camera.read()

        if frame is not None:
            self.process_frame(
                frame
            )

        keyboard_pressed = (
            self.button.is_pressed()
        )

        hardware_pressed = (
            self.hardware.is_button_pressed()
        )

        if (
            (
                keyboard_pressed
                or hardware_pressed
            )
            and not self.rollback_active
        ):
            self.start_rollback()

    def start_rollback(self):
        if self.rollback_active:
            return

        self.rollback_active = True

        self.event_timestamp = (
            time.time()
        )

        self.rollback_start_time = (
            self.event_timestamp
        )

        self.pre_frames = (
            self.buffer.get_recent_frames(
                Config.PRE_SECONDS
            )
        )

        self.pre_audio_chunks = (
            self._get_audio_pre_chunks(
                self.event_timestamp
            )
        )

        self.post_frames = []
        self.post_audio_chunks = []

        self.hardware.set_rollback_state()

        self.logger.info(
            f"Rollback started: "
            f"{len(self.pre_frames)} "
            f"pre frames, "
            f"{len(self.pre_audio_chunks)} "
            f"pre audio chunks, "
            f"event={self.event_timestamp:.6f}"
        )

    def _get_audio_pre_chunks(
        self,
        timestamp
    ):
        start_time = (
            timestamp
            - Config.PRE_SECONDS
        )

        chunks = []

        for (
            chunk_timestamp,
            pcm_data
        ) in self.audio_buffer.get_chunks():

            if (
                start_time
                <= chunk_timestamp
                <= timestamp
            ):
                chunks.append(
                    (
                        chunk_timestamp,
                        pcm_data
                    )
                )

        return chunks

    def finish_rollback(self):
        if not self.rollback_active:
            return

        self.logger.info(
            f"Rollback finished: "
            f"{len(self.pre_frames)} "
            f"pre frames + "
            f"{len(self.post_frames)} "
            f"post frames, "
            f"{len(self.pre_audio_chunks)} "
            f"pre audio chunks + "
            f"{len(self.post_audio_chunks)} "
            f"post audio chunks"
        )

        self.hardware.set_rollback_finished_state()

        try:
            replay = (
                self.replay_manager.save_encoded_av_replay(
                    self.pre_frames,
                    self.post_frames,
                    self.pre_audio_chunks,
                    self.post_audio_chunks,
                    Config.PRE_SECONDS,
                    Config.POST_SECONDS
                )
            )

            if replay:
                self.logger.info(
                    f"Replay saved successfully: "
                    f"{replay.file_path}"
                )

                self.hardware.set_replay_saved_state()

            else:
                self.logger.error(
                    "Replay save failed"
                )

                self.hardware.set_error_state()

        except Exception as error:
            self.logger.error(
                f"Replay save exception: "
                f"{error}"
            )

            self.hardware.set_error_state()

        finally:
            self.pre_frames = []
            self.post_frames = []

            self.pre_audio_chunks = []
            self.post_audio_chunks = []

            self.rollback_active = False
            self.rollback_start_time = None
            self.event_timestamp = None

    def stop(self):
        self.running = False

        self.button.stop()

        if self.camera:
            self.camera.stop()

        self.audio_source.stop()

        self.hardware.stop()

        self.logger.info(
            "LifeReplay system stopped"
        )

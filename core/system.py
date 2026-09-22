import threading
import time

from config.config import Config
from config.settings import Settings
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

        Config.reload()

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

        self.replay_manager = ReplayManager()
        self.camera = Camera()
        self.button = Button()
        self.hardware = GPIOHardware()

        self.running = False

        self.rollback_active = False
        self.rollback_start_time = None
        self.event_timestamp = None

        self.saving_replay = False

        self.pre_frames = []
        self.post_frames = []
        self.pre_audio_chunks = []
        self.post_audio_chunks = []

        self.settings = Settings.load()

        self.logger.info(
            "LifeReplay system initialized"
        )

    def reload_settings(self):
        new_settings = Settings.load()

        if new_settings == self.settings:
            return

        if self.rollback_active:
            self.logger.info(
                "Settings changed during rollback; "
                "waiting for rollback to finish"
            )
            return

        old_settings = self.settings

        camera_changed = (
            new_settings["camera_width"]
            != old_settings["camera_width"]
            or
            new_settings["camera_height"]
            != old_settings["camera_height"]
            or
            new_settings["camera_fps"]
            != old_settings["camera_fps"]
        )

        buffer_changed = (
            new_settings["buffer_seconds"]
            != old_settings["buffer_seconds"]
        )

        Config.reload()

        if buffer_changed:
            old_buffer = self.buffer

            self.buffer = ReplayBuffer(
                Config.BUFFER_SECONDS
            )

            old_buffer.close()

            self.audio_buffer = AudioBuffer(
                Config.BUFFER_SECONDS
            )

            self.logger.info(
                "Replay buffers recreated: "
                f"{Config.BUFFER_SECONDS}s"
            )

        if camera_changed and self.running:
            try:
                self.camera.restart()

                self.audio_source.stop()

                self.audio_source = FakeAudioSource(
                    sample_rate=16000,
                    channels=1,
                    chunk_duration=(
                        1.0 / Config.CAMERA_FPS
                    )
                )

                self.audio_source.start()

                self.logger.info(
                    "Camera settings applied"
                )

            except Exception as error:
                self.logger.error(
                    f"Failed to apply camera settings: "
                    f"{error}"
                )

        self.settings = new_settings

    def process_audio(self):
        audio_result = self.audio_source.read()

        if audio_result is None:
            return

        timestamp, pcm_data = audio_result

        self.audio_buffer.add_chunk(
            timestamp,
            pcm_data
        )

        if self.rollback_active:
            self.post_audio_chunks.append(
                (timestamp, pcm_data)
            )

    def process_frame(self, frame):
        frame_timestamp = time.time()

        if Settings.load().get(
            "replay_buffer_enabled",
            True
        ):
            self.buffer.add_frame(
                frame,
                frame_timestamp
            )

        if self.rollback_active:
            target_timestamp = (
                self.event_timestamp
                + Config.POST_SECONDS
            )

            latest_timestamp = (
                self.buffer.get_latest_timestamp()
            )

            if (
                latest_timestamp is not None
                and latest_timestamp >= target_timestamp
            ):
                self.finish_rollback(
                    target_timestamp
                )

    def start(self):
        self.running = True

        Config.reload()
        self.settings = Settings.load()

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

        self.reload_settings()

        self.process_audio()

        frame = self.camera.read()

        if frame is not None:
            self.process_frame(frame)

        keyboard_pressed = self.button.is_pressed()
        hardware_pressed = (
            self.hardware.is_button_pressed()
        )

        if (
            (
                keyboard_pressed
                or hardware_pressed
            )
            and not self.rollback_active
            and not self.saving_replay
        ):
            self.start_rollback()

    def start_rollback(self):
        if self.rollback_active:
            return

        if self.saving_replay:
            self.logger.info(
                "Rollback ignored: "
                "previous replay is still being saved"
            )
            return

        if not Settings.load().get(
            "replay_buffer_enabled",
            True
        ):
            self.logger.info(
                "Rollback ignored: "
                "replay buffer disabled"
            )
            return

        self.rollback_active = True

        self.event_timestamp = time.time()

        self.rollback_start_time = (
            self.event_timestamp
        )

        pre_start_timestamp = (
            self.event_timestamp
            - Config.PRE_SECONDS
        )

        self.pre_frames = (
            self.buffer.get_frames_between_with_timestamps(
                pre_start_timestamp,
                self.event_timestamp
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

    def _get_audio_pre_chunks(self, timestamp):
        start_time = (
            timestamp
            - Config.PRE_SECONDS
        )

        return self.audio_buffer.get_chunks_between(
            start_time,
            timestamp
        )

    def finish_rollback(
        self,
        target_timestamp=None
    ):
        if not self.rollback_active:
            return

        if target_timestamp is None:
            target_timestamp = time.time()

        self.post_frames = (
            self.buffer.get_frames_between_with_timestamps(
                self.event_timestamp,
                target_timestamp
            )
        )

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

        pre_frames = list(self.pre_frames)
        post_frames = list(self.post_frames)
        pre_audio_chunks = list(self.pre_audio_chunks)
        post_audio_chunks = list(self.post_audio_chunks)

        pre_seconds = Config.PRE_SECONDS
        post_seconds = Config.POST_SECONDS

        self.hardware.set_rollback_finished_state()

        self.pre_frames = []
        self.post_frames = []
        self.pre_audio_chunks = []
        self.post_audio_chunks = []

        self.rollback_active = False
        self.rollback_start_time = None
        self.event_timestamp = None

        self.saving_replay = True

        self.logger.info(
            "Replay captured. "
            "Starting background MP4 save..."
        )

        save_thread = threading.Thread(
            target=self._save_replay_worker,
            args=(
                pre_frames,
                post_frames,
                pre_audio_chunks,
                post_audio_chunks,
                pre_seconds,
                post_seconds,
            ),
            name="ReplaySaveWorker",
            daemon=True,
        )

        save_thread.start()

    def _save_replay_worker(
        self,
        pre_frames,
        post_frames,
        pre_audio_chunks,
        post_audio_chunks,
        pre_seconds,
        post_seconds,
    ):
        try:
            replay = (
                self.replay_manager.save_encoded_av_replay(
                    pre_frames,
                    post_frames,
                    pre_audio_chunks,
                    post_audio_chunks,
                    pre_seconds,
                    post_seconds
                )
            )

            if replay:
                self.logger.info(
                    f"Background replay save completed: "
                    f"{replay.file_path}"
                )

                self.hardware.set_replay_saved_state()

            else:
                self.logger.error(
                    "Background replay save failed"
                )

                self.hardware.set_error_state()

        except Exception as error:
            self.logger.error(
                f"Background replay save exception: "
                f"{error}"
            )

            self.hardware.set_error_state()

        finally:
            self.saving_replay = False

    def stop(self):
        self.running = False

        self.button.stop()

        if self.camera:
            self.camera.stop()

        self.audio_source.stop()
        self.hardware.stop()

        self.buffer.close()

        self.logger.info(
            "LifeReplay system stopped"
        )

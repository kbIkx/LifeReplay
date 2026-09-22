import os
from pathlib import Path
import json
import time
import uuid
import subprocess
import tempfile
import wave

import cv2
import numpy as np

from config.config import Config
from core.logger import Logger
from storage.replay import Replay
from audio.wav_writer import WavWriter


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

        self.metadata_path = os.path.join(
            self.replay_path,
            "metadata"
        )

        os.makedirs(
            self.metadata_path,
            exist_ok=True
        )

    def _metadata_file_path(
        self,
        replay_id
    ):
        return os.path.join(
            self.metadata_path,
            f"{replay_id}.json"
        )

    def _save_metadata(
        self,
        replay
    ):
        metadata = {
            "id": replay.replay_id,
            "created_at": replay.created_at,
            "duration_seconds": replay.duration_seconds,
            "file_size_bytes": replay.file_size_bytes,
            "pre_seconds": replay.pre_seconds,
            "post_seconds": replay.post_seconds,
            "width": replay.width,
            "height": replay.height,
            "fps": replay.fps,
            "frame_count": replay.frame_count,
            "audio": replay.audio,
            "audio_sample_rate": replay.audio_sample_rate,
            "audio_channels": replay.audio_channels,
            "file_path": replay.file_path
        }

        metadata_file = self._metadata_file_path(
            replay.replay_id
        )

        try:
            with open(
                metadata_file,
                "w",
                encoding="utf-8"
            ) as file:
                json.dump(
                    metadata,
                    file,
                    indent=4
                )

            self.logger.info(
                f"Replay metadata saved: "
                f"{metadata_file}"
            )

            return True

        except Exception as error:
            self.logger.error(
                f"Failed to save replay metadata: "
                f"{error}"
            )

            return False

    def _load_metadata(
        self,
        replay_id
    ):
        metadata_file = self._metadata_file_path(
            replay_id
        )

        if not os.path.isfile(
            metadata_file
        ):
            return None

        try:
            with open(
                metadata_file,
                "r",
                encoding="utf-8"
            ) as file:
                return json.load(file)

        except Exception as error:
            self.logger.warning(
                f"Failed to load replay metadata "
                f"{replay_id}: {error}"
            )

            return None

    def _create_replay_from_metadata(
        self,
        metadata,
        file_path
    ):
        return Replay(
            replay_id=metadata.get(
                "id",
                Path(file_path).stem.replace(
                    "replay_",
                    "",
                    1
                )
            ),
            created_at=metadata.get(
                "created_at",
                os.path.getmtime(file_path)
            ),
            pre_seconds=metadata.get(
                "pre_seconds",
                Config.PRE_SECONDS
            ),
            post_seconds=metadata.get(
                "post_seconds",
                Config.POST_SECONDS
            ),
            frame_count=metadata.get(
                "frame_count",
                0
            ),
            duration_seconds=metadata.get(
                "duration_seconds",
                0.0
            ),
            file_path=file_path,
            file_size_bytes=metadata.get(
                "file_size_bytes",
                os.path.getsize(file_path)
            ),
            width=metadata.get(
                "width",
                0
            ),
            height=metadata.get(
                "height",
                0
            ),
            fps=metadata.get(
                "fps",
                0.0
            ),
            audio=metadata.get(
                "audio",
                False
            ),
            audio_sample_rate=metadata.get(
                "audio_sample_rate",
                0
            ),
            audio_channels=metadata.get(
                "audio_channels",
                0
            )
        )

    def _decode_frame(
        self,
        encoded_frame
    ):
        if encoded_frame is None:
            return None

        # New timestamp-aware format:
        # (capture_timestamp, jpeg_bytes)
        if (
            isinstance(encoded_frame, tuple)
            and len(encoded_frame) == 2
        ):
            encoded_frame = encoded_frame[1]

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
            "ultrafast",

            "-threads",
            "2",

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

            return (
                0,
                len(pre_frames) + len(post_frames)
            )

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

    def _write_mp4_with_audio(
        self,
        file_path,
        pre_frames,
        post_frames,
        pre_audio_chunks,
        post_audio_chunks,
        width,
        height,
        fps
    ):
        all_frames = (
            list(pre_frames)
            + list(post_frames)
        )

        all_audio_chunks = (
            list(pre_audio_chunks)
            + list(post_audio_chunks)
        )

        if not all_frames:
            self.logger.error(
                "Cannot create A/V replay "
                "without video frames"
            )

            return (
                0,
                0
            )

        if not all_audio_chunks:
            self.logger.error(
                "Cannot create A/V replay "
                "without audio chunks"
            )

            return (
                0,
                len(all_frames)
            )

        # Keep frames in capture-time order.
        # ReplayBuffer normally already provides this order,
        # but workers can finish JPEG encoding in different order.
        timestamped_frames = [
            frame
            for frame in all_frames
            if (
                isinstance(frame, tuple)
                and len(frame) == 2
            )
        ]

        if timestamped_frames:
            all_frames.sort(
                key=lambda item: item[0]
                if (
                    isinstance(item, tuple)
                    and len(item) == 2
                )
                else float("inf")
            )

        # First video capture timestamp becomes our A/V time zero.
        video_start_timestamp = None

        if all_frames:
            first_frame_item = all_frames[0]

            if (
                isinstance(first_frame_item, tuple)
                and len(first_frame_item) == 2
            ):
                video_start_timestamp = (
                    first_frame_item[0]
                )

        # Keep audio in timestamp order as well.
        timestamped_audio = [
            chunk
            for chunk in all_audio_chunks
            if (
                isinstance(chunk, tuple)
                and len(chunk) == 2
            )
        ]

        if timestamped_audio:
            all_audio_chunks.sort(
                key=lambda item: item[0]
                if (
                    isinstance(item, tuple)
                    and len(item) == 2
                )
                else float("inf")
            )

        # If timestamps are unavailable, preserve backward compatibility.
        # In the current LifeReplay pipeline timestamps are always present.
        if video_start_timestamp is None:
            first_audio = all_audio_chunks[0]

            if (
                isinstance(first_audio, tuple)
                and len(first_audio) == 2
            ):
                video_start_timestamp = first_audio[0]
            else:
                video_start_timestamp = time.time()

            self.logger.warning(
                "A/V replay has no video timestamps; "
                "using audio timestamp as reference"
            )

        video_duration = (
            len(all_frames) / fps
            if fps > 0
            else 0
        )

        if video_duration <= 0:
            self.logger.error(
                "Invalid A/V video duration"
            )

            return (
                0,
                len(all_frames)
            )

        # ---------------------------------------------------------
        # Build a timestamp-aligned WAV.
        #
        # The first audio timestamp is compared with the first
        # video timestamp. If audio starts later, silence is added.
        # If audio starts earlier, the leading samples are trimmed.
        #
        # After alignment, the WAV is exactly the expected CFR
        # video duration. This makes FFmpeg's -shortest a safety
        # mechanism instead of the thing deciding A/V duration.
        # ---------------------------------------------------------

        sample_rate = 16000
        channels = 1
        sample_width = 2
        bytes_per_sample = (
            channels * sample_width
        )

        total_samples = int(
            round(
                video_duration
                * sample_rate
            )
        )

        if total_samples <= 0:
            self.logger.error(
                "Invalid target audio sample count"
            )

            return (
                0,
                len(all_frames)
            )

        aligned_audio = bytearray(
            total_samples
            * bytes_per_sample
        )

        first_audio_timestamp = None

        for audio_chunk in all_audio_chunks:
            if (
                isinstance(audio_chunk, tuple)
                and len(audio_chunk) == 2
            ):
                timestamp, pcm_data = audio_chunk
            else:
                # Legacy raw PCM chunk without timestamp.
                if first_audio_timestamp is None:
                    first_audio_timestamp = (
                        video_start_timestamp
                    )

                timestamp = (
                    first_audio_timestamp
                )
                pcm_data = audio_chunk

            if pcm_data is None:
                continue

            if not isinstance(
                pcm_data,
                (bytes, bytearray)
            ):
                continue

            if len(pcm_data) == 0:
                continue

            if first_audio_timestamp is None:
                first_audio_timestamp = timestamp

            # Number of samples from the beginning of the video
            # until this audio chunk starts.
            offset_samples = int(
                round(
                    (
                        timestamp
                        - video_start_timestamp
                    )
                    * sample_rate
                )
            )

            source_start_sample = 0

            # Audio begins before the first video frame.
            if offset_samples < 0:
                source_start_sample = (
                    -offset_samples
                )
                offset_samples = 0

            chunk_sample_count = (
                len(pcm_data)
                // bytes_per_sample
            )

            if chunk_sample_count <= source_start_sample:
                continue

            if offset_samples >= total_samples:
                continue

            available_samples = (
                total_samples
                - offset_samples
            )

            copy_sample_count = min(
                chunk_sample_count
                - source_start_sample,
                available_samples
            )

            if copy_sample_count <= 0:
                continue

            source_start_byte = (
                source_start_sample
                * bytes_per_sample
            )

            destination_start_byte = (
                offset_samples
                * bytes_per_sample
            )

            copy_byte_count = (
                copy_sample_count
                * bytes_per_sample
            )

            aligned_audio[
                destination_start_byte:
                destination_start_byte
                + copy_byte_count
            ] = pcm_data[
                source_start_byte:
                source_start_byte
                + copy_byte_count
            ]

        if first_audio_timestamp is None:
            self.logger.error(
                "No valid audio timestamps/chunks found"
            )

            return (
                0,
                len(all_frames)
            )

        audio_offset = (
            first_audio_timestamp
            - video_start_timestamp
        )

        self.logger.info(
            "A/V timestamp alignment: "
            f"video_start={video_start_timestamp:.6f}, "
            f"audio_start={first_audio_timestamp:.6f}, "
            f"audio_offset={audio_offset:+.6f}s, "
            f"video_duration={video_duration:.6f}s"
        )

        temp_wav_path = None

        try:
            with tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False
            ) as temp_file:
                temp_wav_path = (
                    temp_file.name
                )

            try:
                with wave.open(
                    temp_wav_path,
                    "wb"
                ) as wav_file:
                    wav_file.setnchannels(
                        channels
                    )

                    wav_file.setsampwidth(
                        sample_width
                    )

                    wav_file.setframerate(
                        sample_rate
                    )

                    wav_file.writeframes(
                        aligned_audio
                    )

            except Exception as error:
                self.logger.error(
                    f"Failed to create aligned WAV: "
                    f"{error}"
                )

                return (
                    0,
                    len(all_frames)
                )

            command = [
                self.ffmpeg_path,
                "-y",

                "-f",
                "mjpeg",

                "-framerate",
                str(fps),

                "-i",
                "-",

                "-i",
                temp_wav_path,

                "-map",
                "0:v:0",

                "-map",
                "1:a:0",

                "-c:v",
                "h264_v4l2m2m",

                "-pix_fmt",
                "yuv420p",

                "-c:a",
                "aac",

                "-b:a",
                "128k",

                "-ar",
                "16000",

                "-ac",
                "1",

                "-t",
                f"{video_duration:.6f}",

                "-shortest",

                "-movflags",
                "+faststart",

                file_path
            ]

            self.logger.info(
                "Using timestamp-aligned "
                "JPEG/MJPEG + WAV FFmpeg input"
            )

            try:
                process = subprocess.Popen(
                    command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE
                )

            except Exception as error:
                self.logger.error(
                    f"Failed to start FFmpeg "
                    f"A/V: {error}"
                )

                return (
                    0,
                    len(all_frames)
                )

            written_frame_count = 0
            failed_frame_count = 0

            pipe_time = 0.0

            try:
                for frame_item in all_frames:
                    if frame_item is None:
                        failed_frame_count += 1
                        continue

                    if (
                        isinstance(frame_item, tuple)
                        and len(frame_item) == 2
                    ):
                        encoded_frame = (
                            frame_item[1]
                        )
                    else:
                        encoded_frame = frame_item

                    if not encoded_frame:
                        failed_frame_count += 1
                        continue

                    try:
                        pipe_start = (
                            time.perf_counter()
                        )

                        process.stdin.write(
                            encoded_frame
                        )

                        pipe_time += (
                            time.perf_counter()
                            - pipe_start
                        )

                        written_frame_count += 1

                    except (
                        BrokenPipeError,
                        OSError
                    ):
                        failed_frame_count += 1

                        self.logger.error(
                            "FFmpeg A/V MJPEG pipe "
                            "closed unexpectedly"
                        )

                        break

            finally:
                if process.stdin is not None:
                    try:
                        process.stdin.close()
                    except OSError:
                        pass

            finalize_start = (
                time.perf_counter()
            )

            stderr_output = (
                process.stderr.read()
                if process.stderr is not None
                else b""
            )

            return_code = process.wait()

            finalize_time = (
                time.perf_counter()
                - finalize_start
            )

            self.logger.info(
                "A/V encoding profile: "
                f"MJPEG pipe={pipe_time:.2f}s, "
                f"finalize/wait={finalize_time:.2f}s"
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
                    f"FFmpeg A/V failed with "
                    f"exit code {return_code}"
                )

                self.logger.error(
                    f"FFmpeg A/V output: "
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
                    len(all_frames)
                )

            self.logger.info(
                "A/V replay written: "
                f"frames={written_frame_count}, "
                f"failed={failed_frame_count}, "
                f"audio_samples={total_samples}"
            )

            return (
                written_frame_count,
                failed_frame_count
            )

        finally:
            if (
                temp_wav_path is not None
                and os.path.isfile(
                    temp_wav_path
                )
            ):
                try:
                    os.remove(
                        temp_wav_path
                    )
                except OSError:
                    self.logger.warning(
                        f"Failed to remove "
                        f"temporary WAV: "
                        f"{temp_wav_path}"
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
            file_path=file_path,
            file_size_bytes=os.path.getsize(
                file_path
            ),
            width=width,
            height=height,
            fps=fps,
            audio=False,
            audio_sample_rate=0,
            audio_channels=0
        )

        self._save_metadata(
            replay
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

    def save_encoded_av_replay(
        self,
        pre_frames,
        post_frames,
        pre_audio_chunks,
        post_audio_chunks,
        pre_seconds,
        post_seconds
    ):
        if not pre_frames and not post_frames:
            self.logger.warning(
                "Cannot save empty A/V replay"
            )

            return None

        if not pre_audio_chunks and not post_audio_chunks:
            self.logger.warning(
                "Cannot save A/V replay "
                "without audio"
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

        expected_audio_chunk_count = (
            len(pre_audio_chunks)
            + len(post_audio_chunks)
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
                "A/V replay frame"
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
            f"Starting A/V MP4 encoding: "
            f"{file_path}"
        )

        self.logger.info(
            f"Video parameters: "
            f"{width}x{height} @ {fps} FPS"
        )

        self.logger.info(
            f"Audio parameters: "
            f"{expected_audio_chunk_count} chunks "
            f"@ 16000 Hz mono"
        )

        (
            written_frame_count,
            failed_frame_count
        ) = self._write_mp4_with_audio(
            file_path=file_path,
            pre_frames=pre_frames,
            post_frames=post_frames,
            pre_audio_chunks=pre_audio_chunks,
            post_audio_chunks=post_audio_chunks,
            width=width,
            height=height,
            fps=fps
        )

        if written_frame_count == 0:
            self.logger.error(
                "No frames were written "
                "to A/V MP4"
            )

            return None

        if not os.path.isfile(
            file_path
        ):
            self.logger.error(
                "A/V MP4 file was not created"
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
            file_path=file_path,
            file_size_bytes=os.path.getsize(
                file_path
            ),
            width=width,
            height=height,
            fps=fps,
            audio=True,
            audio_sample_rate=16000,
            audio_channels=1
        )

        self._save_metadata(
            replay
        )

        self.logger.info(
            f"A/V replay saved: "
            f"{replay.file_path}"
        )

        self.logger.info(
            f"A/V replay frames: "
            f"expected={expected_frame_count}, "
            f"written={written_frame_count}, "
            f"failed={failed_frame_count}"
        )

        self.logger.info(
            f"A/V replay audio chunks: "
            f"{expected_audio_chunk_count}"
        )

        self.logger.info(
            f"A/V replay duration: "
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
            extension_length = 4

            replay_id = filename[
                7:-extension_length
            ]

            file_path = os.path.join(
                self.replay_path,
                filename
            )

            metadata = self._load_metadata(
                replay_id
            )

            if metadata is not None:
                replays.append(
                    self._create_replay_from_metadata(
                        metadata,
                        file_path
                    )
                )

                continue

            created_at = (
                os.path.getmtime(
                    file_path
                )
            )

            frame_count = 0
            fps = Config.CAMERA_FPS
            width = 0
            height = 0
            audio = False
            audio_sample_rate = 0
            audio_channels = 0

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

                width = int(
                    capture.get(
                        cv2.CAP_PROP_FRAME_WIDTH
                    )
                )

                height = int(
                    capture.get(
                        cv2.CAP_PROP_FRAME_HEIGHT
                    )
                )

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
                file_path=file_path,
                file_size_bytes=os.path.getsize(
                    file_path
                ),
                width=width,
                height=height,
                fps=fps,
                audio=audio,
                audio_sample_rate=audio_sample_rate,
                audio_channels=audio_channels
            )

            replays.append(
                replay
            )

            self._save_metadata(
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

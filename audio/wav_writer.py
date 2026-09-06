import wave


class WavWriter:

    @staticmethod
    def write(
        file_path,
        chunks,
        sample_rate=16000,
        channels=1,
        sample_width=2
    ):
        if not chunks:
            return False

        try:
            with wave.open(
                file_path,
                "wb"
            ) as wav:

                wav.setnchannels(
                    channels
                )

                wav.setsampwidth(
                    sample_width
                )

                wav.setframerate(
                    sample_rate
                )

                for _, pcm_data in chunks:
                    wav.writeframes(
                        pcm_data
                    )

            return True

        except Exception:
            return False

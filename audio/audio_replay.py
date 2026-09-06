class AudioReplay:

    def __init__(
        self,
        buffer
    ):
        self.buffer = buffer

    def get_pre_chunks(
        self,
        timestamp,
        seconds
    ):
        start_time = (
            timestamp - seconds
        )

        chunks = []

        for (
            chunk_timestamp,
            pcm_data
        ) in self.buffer.get_chunks():

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

    def get_post_chunks(
        self,
        start_timestamp,
        seconds
    ):
        end_time = (
            start_timestamp + seconds
        )

        chunks = []

        for (
            chunk_timestamp,
            pcm_data
        ) in self.buffer.get_chunks():

            if (
                start_timestamp
                < chunk_timestamp
                <= end_time
            ):
                chunks.append(
                    (
                        chunk_timestamp,
                        pcm_data
                    )
                )

        return chunks

    def combine(
        self,
        pre_chunks,
        post_chunks
    ):
        return (
            pre_chunks
            + post_chunks
        )

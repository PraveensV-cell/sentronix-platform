from src.streaming.stream import CameraStream


class StreamManager:
    """
    Manages all camera streams.
    """

    def __init__(self):
        self.streams = {}

    def start_stream(
        self,
        camera_id: int,
        rtsp_url: str,
    ):

        if camera_id in self.streams:
            return self.streams[camera_id]

        stream = CameraStream(
            camera_id,
            rtsp_url,
        )

        stream.start()

        self.streams[camera_id] = stream

        return stream

    def stop_stream(
        self,
        camera_id: int,
    ):

        stream = self.streams.get(camera_id)

        if stream:
            stream.stop()

            del self.streams[camera_id]

    def get_stream(
        self,
        camera_id: int,
    ):

        return self.streams.get(camera_id)

    def stop_all(self):

        for stream in self.streams.values():
            stream.stop()

        self.streams.clear()


stream_manager = StreamManager()

from pathlib import Path

import cv2

from flask import (
    Flask,
    jsonify,
    send_file,
    Response
)

from core.replay_service import ReplayService
from storage.replay_manager import ReplayManager


app = Flask(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


replay_manager = ReplayManager()

replay_service = ReplayService(
    replay_manager
)


def find_replay(replay_id):

    replays = (
        replay_service.get_replays()
    )

    for replay in replays:

        if replay.replay_id == replay_id:
            return replay

    return None


def get_replay_path(replay):

    replay_path = Path(
        replay.file_path
    )

    if not replay_path.is_absolute():

        replay_path = (
            PROJECT_ROOT /
            replay_path
        )

    return replay_path.resolve()


@app.route("/api/status")
def status():

    return jsonify(
        {
            "name": "LifeReplay",
            "status": "online"
        }
    )


@app.route("/api/replays")
def get_replays():

    replays = (
        replay_service.get_replays()
    )

    result = []

    for replay in replays:

        result.append(
            {
                "id": replay.replay_id,
                "created_at": replay.created_at,
                "pre_seconds": replay.pre_seconds,
                "post_seconds": replay.post_seconds,
                "frame_count": replay.frame_count,
                "duration_seconds": (
                    replay.duration_seconds
                )
            }
        )

    return jsonify(
        result
    )


@app.route(
    "/api/replays/<replay_id>/video"
)
def get_replay_video(
    replay_id
):

    replay = find_replay(
        replay_id
    )

    if replay is None:

        return jsonify(
            {
                "error": "Replay not found"
            }
        ), 404

    replay_path = get_replay_path(
        replay
    )

    if not replay_path.is_file():

        return jsonify(
            {
                "error": "Replay file not found",
                "path": str(replay_path)
            }
        ), 404

    if replay_path.suffix.lower() == ".mp4":

        mimetype = "video/mp4"

    elif replay_path.suffix.lower() == ".avi":

        mimetype = "video/x-msvideo"

    else:

        mimetype = "application/octet-stream"

    return send_file(
        replay_path,
        mimetype=mimetype,
        as_attachment=False
    )


@app.route(
    "/api/replays/<replay_id>/thumbnail"
)
def get_replay_thumbnail(
    replay_id
):

    replay = find_replay(
        replay_id
    )

    if replay is None:

        return jsonify(
            {
                "error": "Replay not found"
            }
        ), 404

    replay_path = get_replay_path(
        replay
    )

    if not replay_path.is_file():

        return jsonify(
            {
                "error": "Replay file not found",
                "path": str(replay_path)
            }
        ), 404

    capture = cv2.VideoCapture(
        str(replay_path)
    )

    if not capture.isOpened():

        return jsonify(
            {
                "error": "Failed to open replay"
            }
        ), 500

    try:

        success, frame = (
            capture.read()
        )

    finally:

        capture.release()

    if not success or frame is None:

        return jsonify(
            {
                "error": "Failed to read replay frame"
            }
        ), 500

    success, encoded = (
        cv2.imencode(
            ".jpg",
            frame,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                80
            ]
        )
    )

    if not success:

        return jsonify(
            {
                "error": "Failed to encode thumbnail"
            }
        ), 500

    return Response(
        encoded.tobytes(),
        mimetype="image/jpeg"
    )


@app.route(
    "/api/replays/<replay_id>",
    methods=["DELETE"]
)
def delete_replay(
    replay_id
):

    deleted = (
        replay_service.delete_replay(
            replay_id
        )
    )

    if not deleted:

        return jsonify(
            {
                "error": "Replay not found"
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "id": replay_id
        }
    )


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )

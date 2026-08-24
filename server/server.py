from flask import (
    Flask,
    jsonify,
    render_template
)

from core.system import LifeReplaySystem


app = Flask(__name__)

system = LifeReplaySystem()


@app.route("/")
def index():

    return render_template(
        "index.html"
    )


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

    replays = system.get_replays()

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
                ),
                "file_path": replay.file_path
            }
        )

    return jsonify(
        result
    )


@app.route(
    "/api/replays/<replay_id>"
)
def get_replay(replay_id):

    frames = system.get_replay(
        replay_id
    )

    if frames is None:

        return jsonify(
            {
                "error": "Replay not found"
            }
        ), 404

    return jsonify(
        {
            "id": replay_id,
            "frame_count": len(frames),
            "frames": frames
        }
    )


@app.route(
    "/api/replays/<replay_id>",
    methods=["DELETE"]
)
def delete_replay(replay_id):

    deleted = system.delete_replay(
        replay_id
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
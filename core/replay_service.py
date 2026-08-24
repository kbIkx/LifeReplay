from core.logger import Logger


class ReplayService:

    def __init__(self, replay_manager):

        self.logger = Logger()

        self.replay_manager = replay_manager

    def get_replays(self):

        return self.replay_manager.list_replays()

    def get_replay(
        self,
        replay_id
    ):

        return self.replay_manager.load_replay(
            replay_id
        )

    def delete_replay(
        self,
        replay_id
    ):

        return self.replay_manager.delete_replay(
            replay_id
        )
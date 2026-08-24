import logging
import os

from config.config import Config


class Logger:
    def __init__(self):
        log_directory = "logs"
        log_filename = "liferereplay.log"

        os.makedirs(
            log_directory,
            exist_ok=True
        )

        log_path = os.path.join(
            log_directory,
            log_filename
        )

        self.logger = logging.getLogger(
            "LifeReplay"
        )

        self.logger.setLevel(
            logging.INFO
        )

        self.logger.propagate = False

        if self.logger.handlers:
            return

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            formatter
        )

        file_handler = logging.FileHandler(
            log_path,
            encoding="utf-8"
        )

        file_handler.setFormatter(
            formatter
        )

        self.logger.addHandler(
            console_handler
        )

        self.logger.addHandler(
            file_handler
        )

    def info(self, message):
        self.logger.info(
            message
        )

    def warning(self, message):
        self.logger.warning(
            message
        )

    def error(self, message):
        self.logger.error(
            message
        )

    def debug(self, message):
        self.logger.debug(
            message
        )
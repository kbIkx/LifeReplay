import select
import sys
import termios
import tty

from core.logger import Logger


class Button:
    def __init__(self):
        self.logger = Logger()

        self.running = False
        self.old_settings = None

    def start(self):
        if not sys.stdin.isatty():
            self.logger.warning(
                "Standard input is not a terminal"
            )
            return

        self.old_settings = termios.tcgetattr(
            sys.stdin
        )

        tty.setcbreak(
            sys.stdin.fileno()
        )

        self.running = True

        self.logger.info(
            "Keyboard button input started"
        )

    def is_pressed(self):
        if not self.running:
            return False

        readable, _, _ = select.select(
            [sys.stdin],
            [],
            [],
            0
        )

        if not readable:
            return False

        key = sys.stdin.read(1)

        if key == " ":
            self.logger.info(
                "Replay button pressed"
            )

            return True

        return False

    def stop(self):
        if self.old_settings is not None:
            termios.tcsetattr(
                sys.stdin,
                termios.TCSADRAIN,
                self.old_settings
            )

            self.old_settings = None

        self.running = False

        self.logger.info(
            "Keyboard button input stopped"
        )
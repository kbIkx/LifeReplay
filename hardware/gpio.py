from core.logger import Logger


class GPIOHardware:
    GREEN_PIN = 27
    YELLOW_PIN = 22
    RED_PIN = 24
    BUTTON_PIN = 17

    BUZZER_PIN = 23

    def __init__(self):
        self.logger = Logger()

        self.available = False

        self.green_led = None
        self.yellow_led = None
        self.red_led = None
        self.button = None

        self._button_was_pressed = False

        try:
            from gpiozero import LED, Button

            self.green_led = LED(
                self.GREEN_PIN
            )

            self.yellow_led = LED(
                self.YELLOW_PIN
            )

            self.red_led = LED(
                self.RED_PIN
            )

            self.button = Button(
                self.BUTTON_PIN,
                pull_up=True,
                bounce_time=0.05
            )

            self.available = True

            self.logger.info(
                "GPIO hardware initialized"
            )

        except Exception as error:
            self.available = False

            self.logger.warning(
                f"GPIO hardware unavailable: "
                f"{error}"
            )

    def start(self):
        if not self.available:
            return

        self.all_off()

        self.green_on()

        self.logger.info(
            "GPIO hardware started"
        )

    def is_button_pressed(self):
        if not self.available:
            return False

        try:
            pressed = self.button.is_pressed

        except Exception as error:
            self.logger.error(
                f"Failed to read GPIO button: "
                f"{error}"
            )

            return False

        pressed_event = (
            pressed
            and not self._button_was_pressed
        )

        self._button_was_pressed = pressed

        if pressed_event:
            self.logger.info(
                "Physical replay button pressed"
            )

        return pressed_event

    def green_on(self):
        if not self.available:
            return

        self.green_led.on()

    def green_off(self):
        if not self.available:
            return

        self.green_led.off()

    def yellow_on(self):
        if not self.available:
            return

        self.yellow_led.on()

    def yellow_off(self):
        if not self.available:
            return

        self.yellow_led.off()

    def red_on(self):
        if not self.available:
            return

        self.red_led.on()

    def red_off(self):
        if not self.available:
            return

        self.red_led.off()

    def all_off(self):
        if not self.available:
            return

        self.green_led.off()
        self.yellow_led.off()
        self.red_led.off()

    def set_start_state(self):
        if not self.available:
            return

        self.red_off()
        self.yellow_off()
        self.green_on()

    def set_rollback_state(self):
        if not self.available:
            return

        self.green_off()
        self.yellow_on()
        self.red_off()

    def set_rollback_finished_state(self):
        if not self.available:
            return

        self.yellow_off()

    def set_replay_saved_state(self):
        if not self.available:
            return

        self.red_off()
        self.yellow_off()
        self.green_on()

    def set_error_state(self):
        if not self.available:
            return

        self.green_off()
        self.yellow_off()
        self.red_on()

    def stop(self):
        if not self.available:
            return

        try:
            self.all_off()

            self.green_led.close()
            self.yellow_led.close()
            self.red_led.close()
            self.button.close()

            self.logger.info(
                "GPIO hardware stopped"
            )

        except Exception as error:
            self.logger.error(
                f"Failed to stop GPIO hardware: "
                f"{error}"
            )

        finally:
            self.available = False
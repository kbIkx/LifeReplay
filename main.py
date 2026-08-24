import time

from core.system import LifeReplaySystem


def main():
    system = LifeReplaySystem()

    try:
        system.start()

        while True:
            system.update()

            time.sleep(
                0.001
            )

    except KeyboardInterrupt:
        print(
            "\nStopping LifeReplay..."
        )

    finally:
        system.stop()


if __name__ == "__main__":
    main()
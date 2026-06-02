import random
import time

from arduino.app_utils import App, Bridge

print("Hello world!")


def loop() -> None:
    x = random.uniform(0, 1)
    y = random.uniform(-1, 1)

    print(f"send {x=} {y=}")
    Bridge.call("xy", x, y)

    time.sleep(1)


# See: https://docs.arduino.cc/software/app-lab/tutorials/getting-started/#app-run
App.run(user_loop=loop)

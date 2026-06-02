import random
import time

from arduino.app_utils import App, Bridge

print("Hello world!")


def loop() -> None:
    x = random.random()
    y = random.random()

    print(f"send {x=} {y=}")
    Bridge.call("xy", x, y)

    time.sleep(1)


# See: https://docs.arduino.cc/software/app-lab/tutorials/getting-started/#app-run
App.run(user_loop=loop)

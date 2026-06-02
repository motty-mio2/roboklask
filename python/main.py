import random
import time

from arduino.app_utils import App, Bridge

print("Hello world!")


def loop() -> None:
    Bridge.call("xy", random.random(), random.random())

    time.sleep(1)


# See: https://docs.arduino.cc/software/app-lab/tutorials/getting-started/#app-run
App.run(user_loop=loop)

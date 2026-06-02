import random
import time

from arduino.app_utils import App, Bridge

print("Hello world!")


def loop() -> None:
    x = random.random()
    y = random.random()

    Bridge.call("xy", x, y)

    time.sleep(1)


App.run(user_loop=loop)

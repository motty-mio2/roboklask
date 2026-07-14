# Initialize WebUI
# ui = WebUI()
import argparse
from concurrent.futures import ThreadPoolExecutor

from python.domain.model.shared import Shared
from python.infra.transmitter.zenoh_transmitter import ZenohTransmitter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run roboklask Python runtime")
    parser.add_argument(
        "--driver",
        choices=["serial", "bridge"],
        default="bridge",
        help="Communication driver: serial or bridge",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    sh = Shared()

    if args.driver == "serial":
        from python.infra.driver.serial_driver import SerialDriver

        driver = SerialDriver(shared=sh)
    elif args.driver == "bridge":
        from python.infra.driver.bridge_driver import BridgeDriver

        driver = BridgeDriver(shared=sh)
    else:
        raise ValueError(f"Unknown driver: {args.driver}")
    z = ZenohTransmitter(shared=sh)

    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(driver.run)
        executor.submit(z.spin)

    while True:
        pass


if __name__ == "__main__":
    main()

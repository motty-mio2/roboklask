# Initialize WebUI
# ui = WebUI()
import argparse
import random
import time
import threading

from python.domain.model.shared import Shared


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run roboklask Python runtime")
    parser.add_argument(
        "--driver",
        choices=["serial", "bridge"],
        default="bridge",
        help="Communication driver: serial or bridge",
    )
    parser.add_argument(
        "--transmitter",
        choices=["zenoh", "dummy"],
        default="dummy",
        help="Transmitter type: zenoh or dummy",
    )
    parser.add_argument(
        "--no-onnx",
        action="store_true",
        help="Disable ONNX model inference and use dummy coordinates",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    sh = Shared()
    use_onnx = not args.no_onnx

    if args.driver == "serial":
        from python.infra.driver.serial_driver import SerialDriver

        driver = SerialDriver(shared=sh, use_onnx=use_onnx)
    elif args.driver == "bridge":
        from python.infra.driver.bridge_driver import BridgeDriver

        driver = BridgeDriver(shared=sh, use_onnx=use_onnx)
    else:
        raise ValueError(f"Unknown driver: {args.driver}")

    if args.transmitter == "zenoh":
        from python.infra.transmitter.zenoh_transmitter import ZenohTransmitter

        transmitter = ZenohTransmitter(shared=sh)
    elif args.transmitter == "dummy":
        from python.infra.transmitter.dummy_transmitter import DummyTransmitter

        transmitter = DummyTransmitter(shared=sh)
    else:
        raise ValueError(f"Unknown transmitter: {args.transmitter}")

    t_transmitter = threading.Thread(
        target=transmitter.spin,
        name="TransmitterThread",
        daemon=True
    )

    t_transmitter.start()

    try:
        driver.run()
    except KeyboardInterrupt:
        print("Shutting down...", flush=True)


if __name__ == "__main__":
    main()

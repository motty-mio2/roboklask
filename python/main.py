# Initialize WebUI
# ui = WebUI()
from concurrent.futures import ThreadPoolExecutor

from python.domain.model.shared import Shared
from python.infra.driver.bridge_driver import BridgeDriver
from python.infra.transmitter.zenoh_transmitter import ZenohTransmitter


def main():

    sh = Shared()

    b = BridgeDriver(shared=sh)
    z = ZenohTransmitter(shared=sh)

    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(b.run)
        executor.submit(z.spin)

    # b.run()

    # def api_xy(data: dict[str, Any]) -> dict[str, Any]:
    #     """Handle the XY update request from WebUI."""
    #     try:
    #         x = float(data.get("x", 0.5))
    #         y = float(data.get("y", 0.0))

    #         print(f"Action: Updating LED to x={x:.2f}, y={y:.2f}")

    #         # Call Arduino Bridge function
    #         Bridge.call("xy", x, y)

    #         return {"status": "success", "x": x, "y": y}
    #     except Exception as e:
    #         print(f"Error: {e}")
    #         return {"status": "error", "message": str(e)}

    # # Register the API endpoint
    # # Framework likely prepends /api automatically
    # ui.expose_api("POST", "/xy", api_xy)


if __name__ == "__main__":
    main()

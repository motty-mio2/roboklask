from typing import Any

from arduino.app_bricks.web_ui import WebUI
from arduino.app_utils import App, Bridge

# Initialize WebUI
ui = WebUI()


def api_xy(data: dict[str, Any]) -> dict[str, Any]:
    """Handle the XY update request from WebUI."""
    try:
        x = float(data.get("x", 0.5))
        y = float(data.get("y", 0.0))

        print(f"Action: Updating LED to x={x:.2f}, y={y:.2f}")

        # Call Arduino Bridge function
        Bridge.call("xy", x, y)

        return {"status": "success", "x": x, "y": y}
    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error", "message": str(e)}


# Register the API endpoint
# Framework likely prepends /api automatically
ui.expose_api("POST", "/xy", api_xy)


App.run()

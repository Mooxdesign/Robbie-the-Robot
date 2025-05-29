from controller.robot import RobotController
from api.app import app
import uvicorn
import sys
import time

if __name__ == "__main__":
    api_enabled = False
    if '--api' in sys.argv:
        api_enabled = True
    robot = RobotController(debug=True, api_enabled=api_enabled)
    try:
        print("[MAIN] Starting robot controller...")
        robot.start()
        if api_enabled:
            print("[MAIN] Starting API server...")
            uvicorn.run(app, host="0.0.0.0", port=8000)
        else:
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("[MAIN] KeyboardInterrupt received. Shutting down...")
    finally:
        print("[MAIN] Stopping robot controller and cleaning up resources...")
        robot.stop()
        print("[MAIN] Shutdown complete.")

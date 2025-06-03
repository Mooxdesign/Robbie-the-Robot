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

    # Patch robot.leds.show for live LED matrix updates
    try:
        from api.app import update_led_matrix_state, manager, robot_state
        import json, asyncio
        orig_show = robot.leds.show
        def patched_show(*args, **kwargs):
            update_led_matrix_state(robot.leds)
            print("[API] Patched robot.leds.show called, led_matrix updated.")
            # Broadcast updated state to all WebSocket clients
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(manager.broadcast(json.dumps(robot_state)))
                else:
                    loop.run_until_complete(manager.broadcast(json.dumps(robot_state)))
            except Exception as e:
                print(f"[API] Error broadcasting LED matrix update: {e}")
            return orig_show(*args, **kwargs)
        robot.leds.show = patched_show
        print("[API] Patched robot.leds.show for live LED matrix updates.")
    except Exception as e:
        print(f"[API] Error patching robot.leds.show: {e}")

    try:
        print("[MAIN] Starting robot controller...")
        robot.start()
        if api_enabled:
            print("[MAIN] Starting API server...")
            uvicorn.run(app, host="localhost", port=8000)
        else:
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("[MAIN] KeyboardInterrupt received. Shutting down...")
    finally:
        print("[MAIN] Stopping robot controller and cleaning up resources...")
        robot.stop()
        print("[MAIN] Shutdown complete.")

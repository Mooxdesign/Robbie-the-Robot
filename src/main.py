from controller.robot import RobotController
from api.app import app
import uvicorn
import threading
import argparse
from utils.logging import setup_logging

parser = argparse.ArgumentParser(description="Robbie the Robot Main Entry Point")
parser.add_argument('--debug', action='store_true', help='Enable debug logging')
parser.add_argument('--api', action='store_true', help='Enable API server')
args = parser.parse_args()

setup_logging(debug=args.debug)
import logging
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    robot = RobotController(debug=True, api_enabled=args.api)

    # Patch robot.leds.show for live LED matrix updates
    try:
        from api.app import update_led_matrix_state, manager, robot_state
        import json, asyncio
        orig_show = robot.leds.leds.show
        def patched_show(*args, **kwargs):
            logger.info(f"[API] Patched robot.leds.leds.show called, led_matrix updated. Buffer: {robot.leds.leds.buffer.tolist()}")
            update_led_matrix_state(robot.leds.leds)
            # Broadcast updated state to all WebSocket clients
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(manager.broadcast(json.dumps(robot_state)))
                else:
                    loop.run_until_complete(manager.broadcast(json.dumps(robot_state)))
            except Exception as e:
                logger.error(f"[API] Error broadcasting LED matrix update: {e}")
            return orig_show(*args, **kwargs)
        robot.leds.leds.show = patched_show
        logger.info("[API] Patched robot.leds.leds.show for live LED matrix updates.")
    except Exception as e:
        logger.error(f"[API] Error patching robot.leds.show: {e}")

    # ONLY START THIS IN DEBUG MODE
    if args.debug:
        from utils.monitoring import thread_health_auditor, log_resource_usage
        logger.debug("[THREAD AUDIT] Starting thread health auditor...")
        threading.Thread(target=thread_health_auditor, args=(robot, logger, 10), name="ThreadHealthAuditor", daemon=True).start()
        logger.debug("[THREAD AUDIT] Starting resource usage logger...")
        threading.Thread(target=log_resource_usage, daemon=True).start()

    try:
        logger.info("[MAIN] Starting robot controller...")
        robot.start()
        if args.api:
            logger.info("[MAIN] Starting API server...")
            uvicorn.run(app, host="localhost", port=8000)

    except KeyboardInterrupt:
        logger.info("[MAIN] KeyboardInterrupt received. Shutting down...")
    finally:
        logger.info("[MAIN] Stopping robot controller and cleaning up resources...")
        robot.stop()
        logger.info("[MAIN] Shutdown complete.")

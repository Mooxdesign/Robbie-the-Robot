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
    api_enabled = args.api
    try:
        robot = RobotController(debug=True, api_enabled=api_enabled)
    except Exception as e:
        logger.error("[INIT] Exception during RobotController initialization!", exc_info=True)
        raise

    if api_enabled:
        # Set up API callbacks
        try:
            from api import app as api_app
            from api.app import update_led_matrix_state, manager, robot_state
            import json, asyncio

            def api_led_update_callback(leds_controller):
                """Callback to broadcast LED state to API clients."""
                update_led_matrix_state(leds_controller)
                try:
                    if api_app.main_event_loop and api_app.main_event_loop.is_running():
                        asyncio.run_coroutine_threadsafe(manager.broadcast(json.dumps(robot_state)), api_app.main_event_loop)
                    else:
                        logger.debug("[API] Main event loop not available for broadcasting LED matrix update.")
                except Exception as e:
                    logger.error(f"[API] Error broadcasting LED matrix update: {e}")
            
            robot.leds.add_api_update_callback(api_led_update_callback)
            logger.info("[API] Registered callback for live LED matrix updates.")

        except Exception as e:
            logger.error(f"[API] Error setting up API callbacks: {e}")

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
        if api_enabled:
            logger.info("[MAIN] Starting API server...")
            uvicorn.run(app, host="0.0.0.0", port=8000)

    except KeyboardInterrupt:
        logger.info("[MAIN] KeyboardInterrupt received. Shutting down...")
    finally:
        logger.info("[MAIN] Stopping robot controller and cleaning up resources...")
        robot.stop()
        logger.info("[MAIN] Shutdown complete.")

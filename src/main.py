from controller.robot import RobotController
from api.app import app
import uvicorn
import sys
import time
import logging
import threading

# Reduce verbosity from noisy libraries
logging.getLogger('comtypes').setLevel(logging.WARNING)
logging.getLogger('comtypes.client').setLevel(logging.WARNING)
logging.getLogger('comtypes.server').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)

def setup_logging():
    # Truncate (clear) the log file at the start of each run
    with open('robot.log', 'w'):
        pass
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] [%(levelname)s] [%(threadName)s] %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('robot.log', mode='a')
        ]
    )

setup_logging()
logger = logging.getLogger(__name__)
logger.info("[TEST] Logging system initialized and test message written.")


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
            logger.info("[API] Patched robot.leds.show called, led_matrix updated.")
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
        robot.leds.show = patched_show
        logger.info("[API] Patched robot.leds.show for live LED matrix updates.")
    except Exception as e:
        logger.error(f"[API] Error patching robot.leds.show: {e}")

    def log_thread_health():
        import threading
        logger.info("[THREAD AUDIT] ---- Active Thread Dump ----")
        threads = threading.enumerate()
        logger.info(f"[THREAD AUDIT] Total threads: {len(threads)}")
        # for t in threads:
        #     logger.info(f"[THREAD AUDIT] Name: {t.name}, ID: {t.ident}, Daemon: {t.daemon}")
        logger.info("[THREAD AUDIT] --------------------------")
        # Optionally, log key robot module thread status as well
        key_threads = [
            ("VoiceModule", getattr(robot.speech, 'voice', None)),
            ("SpeechToTextModule", getattr(robot.speech, 'speech_to_text', None)),
            ("WakeWord", getattr(robot.speech, 'wake_word', None)),
            ("VisionModule", getattr(robot, 'vision', None)),
            ("MotorModule", getattr(robot, 'motor', None)),
        ]
        for name, obj in key_threads:
            t = getattr(obj, 'thread', None) if hasattr(obj, 'thread') else obj
            if isinstance(t, threading.Thread):
                logger.info(f"[THREAD AUDIT] {name}: is_alive={t.is_alive()} (ID={t.ident})")
            elif hasattr(obj, 'is_running'):
                logger.info(f"[THREAD AUDIT] {name}: is_running={getattr(obj, 'is_running', None)}")
            else:
                logger.info(f"[THREAD AUDIT] {name}: not found or not a thread.")

    def thread_health_auditor(interval=10):
        while True:
            time.sleep(interval)
            log_thread_health()

    # Start background thread for thread health auditing
    auditor_thread = threading.Thread(target=thread_health_auditor, args=(10,), name="ThreadHealthAuditor", daemon=True)
    auditor_thread.start()
    logger.info("[THREAD AUDIT] Background thread health auditor started.")

    try:
        logger.info("[MAIN] Starting robot controller...")
        robot.start()
        if api_enabled:
            logger.info("[MAIN] Starting API server...")
            uvicorn.run(app, host="localhost", port=8000)

    except KeyboardInterrupt:
        logger.info("[MAIN] KeyboardInterrupt received. Shutting down...")
    finally:
        logger.info("[MAIN] Stopping robot controller and cleaning up resources...")
        robot.stop()
        logger.info("[MAIN] Shutdown complete.")

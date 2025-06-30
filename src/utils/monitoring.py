import threading
import time
import logging
import psutil

def log_thread_health(robot, logger=None):
    if logger is None:
        logger = logging.getLogger(__name__)
    key_threads = [
        ("WakeWord", getattr(robot.speech, 'wake_word', None)),
        ("VisionModule", getattr(robot, 'vision', None)),
        ("MotorModule", getattr(robot, 'motor', None)),
    ]
    for name, obj in key_threads:
        t = getattr(obj, 'thread', None) if hasattr(obj, 'thread') else obj
        if isinstance(t, threading.Thread):
            logger.debug(f"[THREAD AUDIT] {name}: is_alive={t.is_alive()} (ID={t.ident})")
        elif hasattr(obj, 'is_running'):
            logger.debug(f"[THREAD AUDIT] {name}: is_running={getattr(obj, 'is_running', None)}")
        else:
            logger.debug(f"[THREAD AUDIT] {name}: not found or not a thread.")

def thread_health_auditor(robot, logger=None, interval=10):
    while True:
        time.sleep(interval)
        log_thread_health(robot, logger)

def log_resource_usage():
    process = psutil.Process()
    while True:
        cpu = process.cpu_percent(interval=1)
        mem = process.memory_info().rss / (1024 * 1024)  # MB
        print(f"[Resource Monitor] CPU: {cpu:.1f}% | RAM: {mem:.1f} MB")
        time.sleep(5)

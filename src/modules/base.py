import threading

class BaseController:
    def __init__(self):
        self._running = True
        self._lock = threading.Lock()

    def cleanup(self):
        """Clean up resources"""
        self._running = False

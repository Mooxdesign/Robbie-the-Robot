# Event/callback utilities for RobotController (expand as needed)

class EventManager:
    def __init__(self):
        self._callbacks = {}

    def add_callback(self, event_name, callback):
        if event_name not in self._callbacks:
            self._callbacks[event_name] = []
        self._callbacks[event_name].append(callback)

    def trigger(self, event_name, *args, **kwargs):
        for cb in self._callbacks.get(event_name, []):
            cb(*args, **kwargs)

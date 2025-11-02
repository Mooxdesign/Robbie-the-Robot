import threading
import time
from typing import Callable, List
import logging

from modules.joystick import Joystick as JoystickModule

logger = logging.getLogger(__name__)

class JoystickController:
    """
    REPL-style joystick poller that reads axes/buttons in a single thread
    and publishes updates via a callback.
    """
    def __init__(self,
                 on_update: Callable[[dict], None],
                 joystick_id: int = 0,
                 poll_hz: float = 60.0,
                 debug: bool = False) -> None:
        self.on_update = on_update
        self.joystick_id = joystick_id
        self.poll_dt = 1.0 / max(1.0, float(poll_hz))
        self.debug = debug

        self._thread: threading.Thread | None = None
        self._running = False
        self._jm: JoystickModule | None = None
        self._last_axes: List[float] | None = None
        self._last_buttons: List[bool] | None = None
        self._last_emit_ts: float = 0.0

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, name="JoystickController", daemon=True)
        self._thread.start()
        if self.debug:
            logger.info("[JoystickController] Started")

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
            if self.debug:
                logger.info("[JoystickController] Stopped")

    def cleanup(self) -> None:
        self.stop()
        if self._jm:
            try:
                self._jm.cleanup()
            except Exception:
                pass

    def _run(self) -> None:
        # Create the existing joystick module in no-thread mode and drive it here
        try:
            jm = JoystickModule(joystick_id=self.joystick_id, debug=self.debug, run_threaded=False)
            jm.set_snapshot_callback(lambda axes, buttons: self._forward_snapshot(axes, buttons))
            # Do not call jm.start(); we'll poll manually to ensure init+pump+read are in this thread
            self._jm = jm
        except Exception as e:
            if self.debug:
                logger.info(f"[JoystickController] Failed to init module: {e}")
            self._running = False
            return

        # Poll the module once per tick; this mirrors the REPL exactly in this thread
        import time
        while self._running:
            try:
                jm.process_once()
            except Exception:
                pass
            # keepalive: if we have a last snapshot, re-emit every 1s
            try:
                if self._last_axes is not None and (time.time() - self._last_emit_ts) > 1.0:
                    self._forward_snapshot(self._last_axes, self._last_buttons or [])
            except Exception:
                pass
            time.sleep(self.poll_dt)

    def _forward_snapshot(self, axes: List[float], buttons: List[bool]) -> None:
        try:
            self._last_axes = list(axes) if axes is not None else []
            self._last_buttons = list(buttons) if buttons is not None else []
            import time as _t
            self._last_emit_ts = _t.time()
            payload = {
                'joystick': {
                    'connected': bool(self._last_axes) or bool(self._last_buttons),
                    'axes': self._last_axes,
                    'buttons': self._last_buttons,
                }
            }
            self.on_update(payload)
        except Exception:
            pass

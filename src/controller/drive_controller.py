import math

class DriveController:
    def __init__(self, motors, debug: bool = False):
        self.motors = motors
        self.debug = debug
        self._enabled = False

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = bool(enabled)
        if not self._enabled:
            try:
                self.motors.stop()
            except Exception:
                pass

    def is_enabled(self) -> bool:
        return bool(self._enabled)

    def on_joystick_update(self, axes, buttons) -> None:
        try:
            axes = axes or []
            buttons = buttons or []
        except Exception:
            return

        enable_hold = False
        try:
            enable_hold = bool(buttons[0])
        except Exception:
            enable_hold = False

        enabled = self._enabled or enable_hold
        if not enabled:
            try:
                self.motors.set_motor_speeds(0.0, 0.0)
            except Exception:
                pass
            return

        fwd = 0.0
        turn = 0.0
        try:
            fwd = -float(axes[1]) if len(axes) > 1 else 0.0
        except Exception:
            fwd = 0.0
        try:
            turn = float(axes[0]) if len(axes) > 0 else 0.0
        except Exception:
            turn = 0.0

        dz = 0.10
        if abs(fwd) < dz:
            fwd = 0.0
        if abs(turn) < dz:
            turn = 0.0

        left = fwd + turn
        right = fwd - turn

        m = max(1.0, abs(left), abs(right))
        left /= m
        right /= m

        try:
            self.motors.set_motor_speeds(left, right)
        except Exception:
            pass

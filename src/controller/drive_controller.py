import math
import time

class DriveController:
    def __init__(self, motors, debug: bool = False):
        self.motors = motors
        self.debug = debug
        self._enabled = False
        
        # Head control state
        self._head_pan_target = 0.0
        self._head_tilt_target = 0.0
        self._last_head_update = time.time()
        
        # Load head control config
        from config import Config
        config = Config()
        self._head_control_mode = config.get('joystick', 'head_control', 'mode', default='absolute')
        self._head_velocity_speed = config.get('joystick', 'head_control', 'velocity_speed', default=90.0)
        
        # Initialize head position targets from current motor position
        self._initialize_head_position()

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

        # Head control (right thumbstick)
        try:
            pan_axis = float(axes[3]) if len(axes) > 3 else 0.0  # Right thumbstick horizontal
        except Exception:
            pan_axis = 0.0
        try:
            tilt_axis = float(axes[4]) if len(axes) > 4 else 0.0  # Left trigger
        except Exception:
            tilt_axis = 0.0
            
        # Update head position based on control mode
        current_time = time.time()
        dt = current_time - self._last_head_update
        self._last_head_update = current_time
        
        if self._head_control_mode == "velocity":
            # Velocity mode: axis controls speed of movement
            if abs(pan_axis) >= dz:
                self._head_pan_target += pan_axis * self._head_velocity_speed * dt
                self._head_pan_target = max(-90, min(90, self._head_pan_target))
            
            if abs(tilt_axis) >= dz:
                self._head_tilt_target += tilt_axis * 30.0 * dt  # 30 degrees per second max for tilt
                self._head_tilt_target = max(-45, min(45, self._head_tilt_target))
            
            # Always send current target position in velocity mode
            try:
                self.motors.move_head(pan=self._head_pan_target, tilt=self._head_tilt_target)
            except Exception:
                pass
        else:
            # Absolute mode: axis directly controls position
            pan_cmd = None
            tilt_cmd = None
            if abs(pan_axis) >= dz:
                pan_cmd = pan_axis * 90.0
            if abs(tilt_axis) >= dz:
                tilt_cmd = tilt_axis * 30.0
            if pan_cmd is not None or tilt_cmd is not None:
                try:
                    self.motors.move_head(pan=pan_cmd, tilt=tilt_cmd)
                except Exception:
                    pass

        # Arm control (triggers)
        try:
            left_arm_axis = float(axes[5]) if len(axes) > 5 else None
        except Exception:
            left_arm_axis = None
        try:
            right_arm_axis = -float(axes[2]) if len(axes) > 2 else None
        except Exception:
            right_arm_axis = None
        if left_arm_axis is not None:
            if abs(left_arm_axis) >= dz:
                pos = (left_arm_axis + 1.0) * 0.5
                try:
                    self.motors.move_arm('left', pos)
                except Exception:
                    pass
        if right_arm_axis is not None:
            if abs(right_arm_axis) >= dz:
                pos = (right_arm_axis + 1.0) * 0.5
                try:
                    self.motors.move_arm('right', pos)
                except Exception:
                    pass

    def _initialize_head_position(self):
        """Initialize head position targets from current motor position"""
        try:
            # Get current head position from motors
            snapshot = self.motors.snapshot()
            self._head_pan_target = snapshot.get('head_pan', 0.0) or 0.0
            self._head_tilt_target = snapshot.get('head_tilt', 0.0) or 0.0
            if self.debug:
                print(f"Initialized head position: pan={self._head_pan_target}, tilt={self._head_tilt_target}")
        except Exception as e:
            # Default to center position if unable to read current position
            self._head_pan_target = 0.0
            self._head_tilt_target = 0.0
            if self.debug:
                print(f"Failed to initialize head position, using center: {e}")

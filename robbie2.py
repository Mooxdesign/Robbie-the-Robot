import time
import atexit
import board
from adafruit_motorkit import MotorKit
from pprint import pprint
from I2CController import I2CController
import pyjoystick
from pyjoystick.sdl2 import Key, Joystick, run_event_loop

# Initialize the motor kit
# kit = MotorKit(i2c=board.I2C())
# GAMEPAD_AXIS_LEFT_STICK_X = 0
# GAMEPAD_AXIS_LEFT_STICK_Y = 1
# GAMEPAD_AXIS_RIGHT_STICK_X = 3
# GAMEPAD_AXIS_RIGHT_STICK_Y = 4
# GAMEPAD_AXIS_LEFT_SHOULDER = 2
# GAMEPAD_AXIS_RIGHT_SHOULDER = 5

class JoystickControlledCar:

    ARM_1_FULL_DOWN_PULSE = 1700
    ARM_1_FULL_UP_PULSE = 2800

    ARM_2_FULL_DOWN_PULSE = 2100
    ARM_2_FULL_UP_PULSE = 900

    TILT_HORIZONTAL_PULSE = 1600
    TILT_FULL_DOWN_PULSE = 1900
    TILT_FULL_UP_PULSE = 1100

    PAN_CENTER_PULSE = 1600
    PAN_FULL_RIGHT_PULSE = 700
    PAN_FULL_LEFT_PULSE = 2500

    def __init__(self):
        # Initialize Pygame and joystick

        self.controller = I2CController(0x40, debug=False)
        self.controller.setPWMFreq(50)
        
        # self.control_car()
        run_event_loop(self.print_add, self.print_remove, self.gamepad_input)

    def print_add(self, joy):
        print('Added', joy)

    def print_remove(self, joy):
        print('Removed', joy)

    def gamepad_input(self, key):
        value = key.value
        # if abs(value) < 0.1:
        #     return
        name = key.controller_key_name
        if name == 'leftx':
            self.move_head('x', value)
        if name == 'lefty':
            self.move_head('y', value)
        if name == 'lefttrigger':
            self.move_arm('left', value)
        if name == 'righttrigger':
            self.move_arm('right', value)

    def move_head(self, axis, value):
        if(axis == 'x'):
            pan_pulse = self.PAN_CENTER_PULSE - (value * 900)
            self.controller.Set_Pulse(5,pan_pulse)
        else:
            if(value > 0):
                tilt_pulse = self.TILT_HORIZONTAL_PULSE + (value * (self.TILT_FULL_DOWN_PULSE - self.TILT_HORIZONTAL_PULSE))
            else:
                tilt_pulse = self.TILT_HORIZONTAL_PULSE + (value * (self.TILT_HORIZONTAL_PULSE - self.TILT_FULL_UP_PULSE))

            self.controller.Set_Pulse(2,tilt_pulse)

    def move_arm(self, side, value):
        if(side == 'left'):
            arm_1_pulse = self.ARM_1_FULL_DOWN_PULSE + value * (self.ARM_1_FULL_UP_PULSE - self.ARM_1_FULL_DOWN_PULSE)
            # arm_1_pulse = self.ARM_1_FULL_DOWN_PULSE
            self.controller.Set_Pulse(7,arm_1_pulse)
        elif(side == 'right'):
            arm_2_pulse = self.ARM_2_FULL_DOWN_PULSE + value * (self.ARM_2_FULL_UP_PULSE - self.ARM_2_FULL_DOWN_PULSE)
            # arm_2_pulse = self.ARM_2_FULL_DOWN_PULSE
            self.controller.Set_Pulse(8,arm_2_pulse)


    def move_car(self):
        
        # Define the maximum speed for the motors
        max_speed = 1.0
        min_speed = 0.3

        # Read joystick axes
        axis_0 = self.joystick.get_axis(0)  # Left to Right
        axis_1 = self.joystick.get_axis(1)  # Down to Up

        # Read joystick axes
        axis_2 = self.joystick.get_axis(3)  # Left to Right

        # Calculate motor speeds based on joystick inputs
        speed = abs(axis_1)  # Forward/Backward speed
        # Calculate direction for steering
        direction = axis_0

        # Calculate motor speeds based on joystick inputs and steering
        left_speed = right_speed = speed
        if direction > 0:  # Turning right
            left_speed *= 1 - abs(direction)
        elif direction < 0:  # Turning left
            right_speed *= 1 - abs(direction)

        # Reverse if axis_1 is negative
        if self.joystick.get_axis(1) < 0:
            left_speed *= -1
            right_speed *= -1

        # Don't power motors below 0.35
        if abs(left_speed) < min_speed or abs(right_speed) < min_speed:
            left_speed = 0
            right_speed = 0

        if abs(axis_2) > min_speed:
            left_speed = axis_2
            right_speed = -axis_2

        # Control the motors
        # kit.motor1.throttle = left_speed
        # kit.motor2.throttle = left_speed
        # kit.motor3.throttle = right_speed
        # kit.motor4.throttle = right_speed

if __name__ == "__main__":
    car = JoystickControlledCar()
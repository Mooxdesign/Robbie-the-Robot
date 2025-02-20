import pygame
import time
import atexit
import board
from adafruit_motorkit import MotorKit
from I2CController import I2CController

# Initialize the motor kit
# kit = MotorKit(i2c=board.I2C())

class JoystickControlledCar:

    ARM_1_FULL_DOWN_PULSE = 1100
    ARM_1_FULL_UP_PULSE = 2500

    ARM_2_FULL_DOWN_PULSE = 1100
    ARM_2_FULL_UP_PULSE = 2500

    TILT_HORIZONTAL_PULSE = 1600
    TILT_FULL_DOWN_PULSE = 1900
    TILT_FULL_UP_PULSE = 1100

    PAN_CENTER_PULSE = 1600
    PAN_FULL_RIGHT_PULSE = 700
    PAN_FULL_LEFT_PULSE = 2500

    def __init__(self):
        # Initialize Pygame and joystick
        pygame.init()
        pygame.joystick.init()
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        self.controller = I2CController(0x40, debug=False)
        self.controller.setPWMFreq(50)

    def control_car(self):
        while True:
            pygame.event.get()
            # Move the car based on joystick inputs
            # self.move_car()
            self.move_head()
            time.sleep(0.1)  # Add a small delay for stability

    def move_head(self):
        # Read joystick axes
        axis_0 = -self.joystick.get_axis(0)  # Left to Right
        axis_1 = self.joystick.get_axis(1)  # Down to Up

        axis_2 = (self.joystick.get_axis(2) + 1) / 2  # Shoulder Left
        axis_5 = 1 - (self.joystick.get_axis(5) + 1) / 2  # Shoulder Right

        # arm_pulse = 1600 + (axis_3 * 900)
        if axis_2 > -0.1 and axis_2 < 0.1:
            arm_1_pulse = 0
        else:
            arm_1_pulse = self.ARM_1_FULL_DOWN_PULSE + axis_2 * (self.ARM_1_FULL_UP_PULSE - self.ARM_1_FULL_DOWN_PULSE)

        if axis_5 > -0.1 and axis_5 < 0.1:
            arm_2_pulse = 0
        else:
            arm_2_pulse = self.ARM_2_FULL_DOWN_PULSE + axis_5 * (self.ARM_2_FULL_UP_PULSE - self.ARM_2_FULL_DOWN_PULSE)
            


        if axis_2 > -0.1 and axis_2 < 0.1:
            pan_pulse = 0
        else:
            pan_pulse = self.PAN_CENTER_PULSE + (axis_0 * 900)



        self.controller.Set_Pulse(5,pan_pulse)
        self.controller.Set_Pulse(7,arm_1_pulse)
        self.controller.Set_Pulse(8,arm_2_pulse)
        # print('axis_2')
        # print(axis_2)
        # print('axis_5')
        # print(axis_5)
        # print('arm1')
        # print(arm_1_pulse)
        # print('arm2')
        # print(arm_2_pulse)

        if axis_1 > 0:
            tilt_pulse = self.TILT_HORIZONTAL_PULSE + (axis_1 * (self.TILT_FULL_DOWN_PULSE - self.TILT_HORIZONTAL_PULSE))
        elif axis_1 > -0.1 and axis_1 < 0.1:
            tilt_pulse = 0
        else:
            tilt_pulse = self.TILT_HORIZONTAL_PULSE + (axis_1 * (self.TILT_HORIZONTAL_PULSE - self.TILT_FULL_UP_PULSE))

        # print(tilt_pulse)
        self.controller.Set_Pulse(2,tilt_pulse)


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
    car.control_car()



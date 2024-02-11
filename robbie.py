import pygame
import time
import atexit
import board
from adafruit_motorkit import MotorKit

# Initialize the motor kit
kit = MotorKit(i2c=board.I2C())

class JoystickControlledCar:
    def __init__(self):
        # Initialize Pygame and joystick
        pygame.init()
        pygame.joystick.init()
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()

    def control_car(self):
        # Define the maximum speed for the motors
        max_speed = 1.0
        min_speed = 0.3

        while True:
            pygame.event.get()
            
            # Read joystick axes
            axis_0 = self.joystick.get_axis(0)  # Left to Right
            axis_1 = self.joystick.get_axis(1)  # Down to Up

            # Calculate motor speeds based on joystick inputs
            speed = abs(axis_1)  # Forward/Backward speed
            
            # Calculate direction for steering
            direction = axis_0

            # Move the car based on joystick inputs
            self.move_car(speed, direction, max_speed, min_speed)
            time.sleep(0.1)  # Add a small delay for stability

    def move_car(self, speed, direction, max_speed, min_speed):
        if speed < min_speed:
            left_speed = 0
            right_speed = 0
        else:
            left_speed = min(max(speed + direction / 2, min_speed), max_speed)
            right_speed = min(max(speed - direction / 2, min_speed), max_speed)

        # Control the motors
        kit.motor1.throttle = left_speed
        kit.motor2.throttle = left_speed
        kit.motor3.throttle = right_speed
        kit.motor4.throttle = right_speed

if __name__ == "__main__":
    car = JoystickControlledCar()
    car.control_car()

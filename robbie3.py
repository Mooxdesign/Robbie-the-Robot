import time
import atexit
import board
from pprint import pprint
from pyjoystick.sdl2 import Key, Joystick, run_event_loop
from ServoBody import ServoBody

class RobbieTheRobot:

    def __init__(self):
        # Initialize Pygame and joystick

        self.servo_body = ServoBody()
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
            self.servo_body.move_head('x', value)
        if name == 'lefty':
            self.servo_body.move_head('y', value)
        if name == 'lefttrigger':
            self.servo_body.move_arm('left', value)
        if name == 'righttrigger':
            self.servo_body.move_arm('right', value)

if __name__ == "__main__":
    robbie = RobbieTheRobot()
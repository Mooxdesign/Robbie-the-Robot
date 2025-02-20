#!/usr/bin/env python
import pygame
import time
import signal
import sys
import unicornhat as unicorn

class JoystickControlledUnicorn:

    def __init__(self):

        pygame.init()
        # pygame.display.set_mode((1, 1))
        pygame.joystick.init()
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        unicorn.set_layout(unicorn.AUTO)
        unicorn.rotation(0)
        unicorn.brightness(0.4)
        width,height=unicorn.get_shape()

    def control_unicorn(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print('Bye!')
                    pygame.quit()
                    sys.exit()

            self.change_pattern()
            time.sleep(0.1)  # Add a small delay for stability

    def change_pattern(self):
        axis_1 = self.joystick.get_axis(0)  # Down to Up
        axis_2 = self.joystick.get_axis(1)  # Down to Up
        axis_3 = self.joystick.get_axis(4)  # Down to Up
        r = int(255 * abs(axis_1))
        g = int(255 * abs(axis_2))
        b = int(255 * abs(axis_3))

        if self.joystick.get_button(0):
            g = 255
        if self.joystick.get_button(1):
            r = 255
        if self.joystick.get_button(2):
            b = 255
        if self.joystick.get_button(3):
            r = 255
            g = 255
        unicorn.set_all(r,g,b)
        unicorn.show()

def signal_handler(sig, frame):
    print('Exiting...')
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    car = JoystickControlledUnicorn()
    car.control_unicorn()

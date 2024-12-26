import time
import atexit
import board
from adafruit_motorkit import MotorKit

# Initialize the motor kit
kit = MotorKit(i2c=board.I2C())

class TheControlledCar:
    def control_car(self):
        while True:
            kit.motor1.throttle = 1
            kit.motor2.throttle = 1
            kit.motor3.throttle = 1
            kit.motor4.throttle = 1
            time.sleep(1)
            kit.motor1.throttle = -1
            kit.motor2.throttle = -1
            kit.motor3.throttle = -1
            kit.motor4.throttle = -1
            time.sleep(1)

if __name__ == "__main__":
    car = TheControlledCar()
    car.control_car()

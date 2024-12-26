import RPi.GPIO as GPIO
from time import sleep
GPIO.setmode(GPIO.BOARD)
GPIO.setup(16, GPIO.OUT)
pwm=GPIO.PWM(16, 50)
pwm.start(0)

def SetAngle(angle):
	duty = angle / 18 + 2
	GPIO.output(16, True)
	pwm.ChangeDutyCycle(duty)
	sleep(1)
	GPIO.output(16, False)
	pwm.ChangeDutyCycle(0)
	
def moveServo(start,end,delta):  #move from start to end, using delta number of seconds
     incMove=(end-start)/100.0
     incTime=delta/100.0
     for x in range(100):
          GPIO.set_servo_pulsewidth(4, int(start+x*incMove))
          time.sleep(incTime)

SetAngle(10) 
sleep(1)
SetAngle(140) 
sleep(2)
SetAngle(20) 
sleep(2)
SetAngle(150) 
sleep(1)
SetAngle(30) 
sleep(2)
SetAngle(120) 
sleep(2)
SetAngle(10) 
sleep(1)
SetAngle(160) 
sleep(2)
SetAngle(20) 
sleep(2)
pwm.stop()
GPIO.cleanup()
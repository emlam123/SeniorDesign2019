import RPi.GPIO as GPIO
from time import sleep

def signal(right,left):
	print(right,left)
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)
	#right
	GPIO.setup(23, GPIO.OUT, initial=GPIO.LOW)
	#left
	GPIO.setup(24, GPIO.OUT, initial=GPIO.LOW)

	#have separate thread
	if right==True:
		GPIO.output(23,GPIO.HIGH)
		sleep(1)
		GPIO.output(23,GPIO.LOW)
		sleep(1)

	if left==True:
		GPIO.output(24,GPIO.HIGH)
		sleep(1)
		GPIO.output(24,GPIO.LOW)
		sleep(1)

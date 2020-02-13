import RPi.GPIO as GPIO
from time import sleep

def signal(right,left):
    print(right,left)
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    #right
    GPIO.setup(5, GPIO.OUT, initial=GPIO.LOW)
    #left
    GPIO.setup(6, GPIO.OUT, initial=GPIO.LOW)

    #have separate thread
    try:
        if right=="True":
            GPIO.output(5,True)
            sleep(.5)
            GPIO.output(5,False)
            sleep(.5)
        #else:
        #    GPIO.output(5,False)
        if left=="True":
            GPIO.output(6,True)
            sleep(.5)
            GPIO.output(6,False)
            sleep(.5)
        #else:
        #    GPIO.output(6,False)

    finally:
        GPIO.cleanup()






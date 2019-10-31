#!/usr/bin/python


import spidev
import time

delay = 1
channel = 0

spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz=1000000

def readadc(chan):
    if chan<0 or chan>7:
        return False

    reading = spi.xfer2([1,8+chan<<4, 0])
    data = ((reading[1]&3)<<8)+reading[2]
    return data

try: 
    while True: 
        force = readadc(channel)
        print("Pressure Value: %d" %force)
        time.sleep(delay)
except KeyboardInterrupt:
    pass


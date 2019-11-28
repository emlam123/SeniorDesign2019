import spidev
import random
import socket
import time
import datetime
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
    
    #normalize min=0 max=10
    data = (1+(10*data))/1000
    
    
    return data


def Main():
    ip_addr = input("Enter an IP address: ")

    host = ip_addr
    #host = '174.77.60.109'

    port = 12345

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host,port))
    #s.connect(('192.168.0.13', port))

    while True:
        force = readadc(channel)
        print("Pressure Value: %d" %force)
        force = int(force)
        #time.sleep(delay)        
        message = "2:" + str(force) + "\n" + str(datetime.datetime.now().time())
        s.send(message.encode('ascii'))
        time.sleep(.01)
    # close the connection



if __name__ == '__main__':
    Main()

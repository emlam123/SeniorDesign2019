import spidev
import random
import socket
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
    
    #normalize min=0 max=10
    data = (1+(10*data))/1000
    
    
    return data


def Main():
    host = 'localhost'

    port = 8080

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.connect(('192.168.0.13', port))

    while True:
        force = readadc(channel)
        print("Pressure Value: %d" %force)
        time.sleep(delay)        
        message = "2:" + str(force)
        s.send(message.encode('ascii'))

        data = s.recv(1024)

        print('Received from the server :', str(data.decode('ascii')))
    # close the connection



if __name__ == '__main__':
    Main()

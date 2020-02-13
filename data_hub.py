import spidev
import random
import socket
import time
import datetime
delay = 5 

forceChannel = 0
muscleChannel = 1


spi = spidev.SpiDev()
spi.open(0,0)
#spi.max_speed_hz=1000000
spi.max_speed_hz=100000


def readadc(chan):
    if chan<0 or chan>7:
        return False

    reading = spi.xfer2([1,8+chan<<4, 0])
    data = ((reading[1]&3)<<8)+reading[2]
    if(chan == 0):

        print("raw reading for force sensor: ", reading)
        'normalize min=0 max=10'
        data = (1+(10*data))/1000
    
   
    elif(chan == 1):
        print("raw reading for muscle sensor: ", reading)
        'data normalization for muscle sensor 0 to 50'
        data = (1+(50*data))/1000 
    
    return data


def readadc2(chan):
    ''' reading adc channel 2 for muscle sensor'''
    if chan<0 or chan>7:
        return False
    
    reading = spi.xfer2([1,8+chan<<4, 0])
    print("raw reading for muscle sensor: ", reading)
    data = ((reading[1]&3)<<8)+reading[2]
    
    'data normalization for muscle sensor here'
    data = (1+(35*data))/1000 
    return data




def Main():
    ip_addr = input("Enter an IP address: ")

    host = ip_addr
    #host = '174.77.60.109'

    port = 12345

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host,port))
    #s.connect(('192.168.0.13', port))
    
    try:
        while True:
       
            force = readadc(forceChannel)
            print("Pressure Value: %d" %force)
            force = int(force)
        #time.sleep(delay)        

          #  s.send(message.encode('ascii'))
#        time.sleep(.01)

        
            ''' muscle part -still have to normalize the data '''
            muscle = readadc(muscleChannel)
            print("Muscle intensity value: %d" %muscle)
            print("both : %d and %d" %(force ,muscle)) 
            muscle = int(muscle)
        
            message = "2:" + str(force) + "\n" + str(datetime.datetime.now().time())
            message2 = "3:" + str(muscle) + "\n" + str(datetime.datetime.now().time())
            s.send(message.encode('ascii'))
            s.send(message2.encode('ascii'))
            time.sleep(.01)

    except KeyboardInterrupt:
        pass


    # close the connection



if __name__ == '__main__':
    Main()

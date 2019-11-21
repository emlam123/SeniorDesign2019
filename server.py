import socket
import sys
from _thread import *
import threading
import datetime
import csv

print_lock = threading.Lock()


def threaded(c):
    heartrate_queue = [None] * 30
    speed_queue = [None] * 4
    force_queue = [None] * 30

    heartrate_pointer = 0
    speed_pointer = 0
    force_pointer = 0

    heartrate_sum = 0
    speed_sum = 0
    force_sum = 0
    while True:

        data = c.recv(1024)
        if not data:
            print('Bye')
            sys.exit(0)
        message = str(data.decode('ascii'))
        
        # Speed Sensor is flag 1
        if message[0] == "1":
            message = "Speed Sensor Data Received speed(mph) rate: " + message.replace("1:", '')
            print("Received at: " + str(datetime.datetime.now()))
            speed = data.decode().split('1:')
            speed = speed[1].split('\n')
            print(speed[1]) #speed[1] = the actual speed
            speed = int(speed[1])
            
            if (speed>10 and speed<20):
                c.send(("Slow Down").encode())
            elif (speed>20):
                c.send(("Thats fast").encode())
            message = message.replace("1:", '')
            print("Received at: " + str(datetime.datetime.now().time()))
            message = message.split("\n")
            print("hello")
            print(message)
            print(message[0])
            print(message[1])
            print(message[2])
            print("check here" + str(speed_pointer))
            if speed_pointer == 3:
                print("Writing to CSV file")
                speed_queue[speed_pointer] = [message[0], message[1], message[2]] #[0] - msg string, [1] - speed, [2] - date 

                with open('speed_rate_tester.csv', 'a', newline='') as f:
                    writer = csv.writer(f)
                    for data in speed_queue:
                        
                        #print("checking data[0] with typpe : "+str(type(data[0])) + "and  + " + data[1]);
                        print("the data is being written in speed_rate.csv")
                       # speed_sum = speed_sum + int(data[1])
                        writer.writerow(data)
                        
                    

#                with open('average_speed.csv', 'a', newline='') as f:
#                    hello = [float(speed_sum/30),str(datetime.datetime.now().time())]
#                    writer = csv.writer(f)
#                    writer.writerow(hello)
                speed_sum = 0
                speed_pointer = 0
            speed_queue[speed_pointer] = [message[0],str(datetime.datetime.now().time()),message[1]]
            speed_pointer += 1
            print("speed pointer did pass and it was : " + str(speed_pointer))

        # Force Sensor is flag 2
        if message[0] == "2":
            message = message.replace("2:", '')
            print("Force Sensor Data Received at: " + str(datetime.datetime.now().time()))
            message = message.split("\n")
            if force_pointer == 29:
                print("Writing to CSV file")
                force_queue[force_pointer] = [message[0], str(datetime.datetime.now().time()), message[1]]

                with open('force_rate.csv', 'a', newline) as f:
                    writer = csv.writer(f)
                    for data in force_queue:
                        force_sum = force_sum + int(data[0])
                        writer.writerow(data)

                with open('average_force.csv', 'a', newline) as f:
                    hello = [float(force_sum/30),str(datetime.datetime.now().time())]
                    writer = csv.writer(f)
                    writer.writerow(hello)
                force_sum = 0
                force_pointer = 0
            force_queue[force_pointer] = [message[0],str(datetime.datetime.now().time()),message[1]]
            force_pointer = force_pointer + 1

        if message[0] == "3":
            message = "Heart Rate Sensor Data Received heart rate(BPM) rate: " + message.replace("3:", '')
            print("Received at: " + str(datetime.datetime.now()))
            print(message)
        #c.send(message.encode('ascii'))
            message = message.replace("3:", '')
            print("Received at: " + str(datetime.datetime.now().time()))
            message = message.split("\n")
            if heartrate_pointer == 29:
                print("Writing to CSV file")
                heartrate_queue[heartrate_pointer] = [message[0], str(datetime.datetime.now().time()), message[1]]

                with open('heart_rate.csv', 'a', newline='') as f:
                    writer = csv.writer(f)
                    for data in heartrate_queue:
                        heartrate_sum = heartrate_sum + int(data[0])
                        writer.writerow(data)

                with open('average_heartrate.csv', 'a', newline='') as f:
                    hello = [float(heartrate_sum/30),str(datetime.datetime.now().time())]
                    writer = csv.writer(f)
                    writer.writerow(hello)
                heartrate_sum = 0
                heartrate_pointer = 0
            heartrate_queue[heartrate_pointer] = [message[0],str(datetime.datetime.now().time()),message[1]]
            heartrate_pointer = heartrate_pointer + 1


        #c.send("Server Received at".encode('ascii'))
        print("Sent to client at: " + str(datetime.datetime.now()))

    c.close()


def Main():
    try:
        hostname = socket.gethostname()
        print(hostname)
        ipaddr = socket.gethostbyname(hostname)
        print(ipaddr)

        host = "174.77.60.109"
        port = 12345
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((host, port))
        #host = "100.67.113.183"
        #port = 12345
        #s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #s.bind(('100.67.113.183', port))
        print("socket binded to port", port)

        s.listen(5)
        print("socket is listening")

        while True:
            c, addr = s.accept()

            print('Connected to :', addr[0], ':', addr[1])

            start_new_thread(threaded, (c,))
        s.close()
    except KeyboardInterrupt as msg:
        sys.exit(0)


if __name__ == '__main__':
    Main()

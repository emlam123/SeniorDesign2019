import socket
import sys
from _thread import *
import threading
import datetime
import csv

print_lock = threading.Lock()


def threaded(c):
    heartrate_queue = [None] * 30
    speed_queue = [None] * 30
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
            message = message.replace("1:", '')
            print("Received at: " + str(datetime.datetime.now().time()))
            message = message.split("\n")
            if speed_pointer == 29:
                print("Writing to CSV file")
                speed_queue[speed_pointer] = [message[0], str(datetime.datetime.now().time()), message[1]]

                with open('speed_rate.csv', 'a', newline='') as f:
                    writer = csv.writer(f)
                    for data in speed_queue:
                        speed_sum = speed_sum + int(data[0])
                        writer.writerow(data)

                with open('average_speed.csv', 'a', newline='') as f:
                    hello = [float(speed_sum/30),str(datetime.datetime.now().time())]
                    writer = csv.writer(f)
                    writer.writerow(hello)
                speed_sum = 0
                speed_pointer = 0
            speed_queue[speed_pointer] = [message[0],str(datetime.datetime.now().time()),message[1]]
            speed_pointer = speed_pointer + 1

        # Force Sensor is flag 2
        if message[0] == "2":
            message = message.replace("2:", '')
            print("Received at: " + str(datetime.datetime.now().time()))
            message = message.split("\n")
            if force_pointer == 29:
                print("Writing to CSV file")
                force_queue[force_pointer] = [message[0], str(datetime.datetime.now().time()), message[1]]

                with open('force_rate.csv', 'a', newline='') as f:
                    writer = csv.writer(f)
                    for data in force_queue:
                        force_sum = force_sum + int(data[0])
                        writer.writerow(data)

                with open('average_force.csv', 'a', newline='') as f:
                    hello = [float(force_sum/30),str(datetime.datetime.now().time())]
                    writer = csv.writer(f)
                    writer.writerow(hello)
                force_sum = 0
                force_pointer = 0
            force_queue[force_pointer] = [message[0],str(datetime.datetime.now().time()),message[1]]
            force_pointer = force_pointer + 1

        if message[0] == "3":
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


        c.send("Server Received at".encode('ascii'))
        print("Sent to client at: " + str(datetime.datetime.now()))

    c.close()


def Main():
    try:
        host = "100.67.113.183"
        port = 12345
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('100.67.113.183', port))
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

import socket
import sys
from _thread import *
import threading
import datetime
import csv

print_lock = threading.Lock()


def threaded(c):
    heart_rate_queue = []
    speed_queue = [None] * 30
    force_queue = []
    speed_pointer = 0
    heart_rate_pointer = 0
    speed_pointer = 0
    speed_sum = 0

    while True:

        data = c.recv(1024)
        if not data:
            print('Bye')
            sys.exit(0)
        message = str(data.decode('ascii'))

        if message[0] == "1":
            message = message.replace("1:", '')
            print("Received at: " + str(datetime.datetime.now().time()))
            message = message.split("\n")
            if speed_pointer == 29:
                print("Writing to CSV file")
                speed_queue[speed_pointer] = [message[0], str(datetime.datetime.now().time())]

                with open('speed_rate.csv', 'a') as f:
                    writer = csv.writer(f)
                    for data in speed_queue:
                        speed_sum = speed_sum + int(data[0])
                        writer.writerow(data)

                with open('average_speed.csv', 'a') as f:
                    hello = [float(speed_sum/30),str(datetime.datetime.now().time())]
                    writer = csv.writer(f)
                    writer.writerow(hello)
                speed_sum = 0
                speed_pointer = 0
            speed_queue[speed_pointer] = [message[0],str(datetime.datetime.now().time())]
            speed_pointer = speed_pointer + 1

        if message[0] == "2":
            message = "Received force rate: " + message.replace("2:", '')
            print("Received at: " + str(datetime.datetime.now()))

        if message[0] == "3":
            message = "Received heart rate(BPM) rate: " + message.replace("3:", '')
            print("Received at: " + str(datetime.datetime.now()))


        c.send("Server Received at".encode('ascii'))
        print("Sent to client at: " + str(datetime.datetime.now()))

    c.close()


def Main():
    try:
        host = "192.168.1.40"
        port = 12345
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('192.168.1.40', port))
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

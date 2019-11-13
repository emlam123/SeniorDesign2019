import socket
import sys
from _thread import *
import threading
import datetime

print_lock = threading.Lock()


def threaded(c):
    while True:

        data = c.recv(1024)
        if not data:
            print('Bye')
            sys.exit(0)
        message = str(data.decode('ascii'))

        if message[0] == "1":
            message = "Received speed(mph) rate: " + message.replace("1:", '')
            print("Received at: " + str(datetime.datetime.now()))

        if message[0] == "2":
            message = "Received force rate: " + message.replace("2:", '')
            print("Received at: " + str(datetime.datetime.now()))

        if message[0] == "3":
            message = "Received heart rate(BPM) rate: " + message.replace("3:", '')
            print("Received at: " + str(datetime.datetime.now()))
        print(message)
        c.send(message.encode('ascii'))
        print("Sent to client at: " + str(datetime.datetime.now()))
        
    c.close()


def Main():
    try:
        host = "localhost"
        port = 8080
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('192.168.0.13', port))
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

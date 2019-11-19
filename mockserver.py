import socket

s = socket.socket()

s.bind(('localhost',8080))
s.listen(2)
try:
	while True:
		client,addr = s.accept()

		while True:
			data = client.recv(4096)
			print(data.decode())
			speed = data.decode().split('1:')
			speed = speed[1].strip('km/h')
			#speed = speed.strip(' ')
			#speed = speed.strip(' ')
			print(speed)
			speed = int(speed)
			if (speed>10 and speed<20):
				client.send(("Slow Down").encode())
			elif (speed>20):
				client.send(("Thats fast").encode())
except KeyboardInterrupt:
	sys.exit(0)

		



client.close()


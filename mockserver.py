import socket

s = socket.socket()

s.bind(('localhost',8080))
s.listen(2)

while True:
	client,addr = s.accept()

	while True:
		data = client.recv(4096)
		print(data.decode())
		speed = data.decode().strip('1:')
		speed = speed.strip('km/h')
		speed = speed.strip(' ')
		speed = speed.strip(' ')
		print(speed)
		speed = int(speed)
		if (speed>10):
			client.send(("Slow Down").encode())

		



client.close()


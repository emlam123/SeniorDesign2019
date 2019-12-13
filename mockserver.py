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
			d=data.decode()
			if d[0]=='1':
				speed = data.decode().replace('1:','')
				speed = speed.split('\n')
				#speed = speed.strip(' ')
				#speed = speed.strip(' ')
				print(speed[0])
				speed = int(speed[0])
				#if (speed<10):
				#	client.send(("None").encode())
				if (speed>10 and speed<60):
					client.send(("Slow Down").encode())
				elif (speed>60):
					client.send(("Thats fast").encode())
			if d[0]=='3':
				physics = data.decode().replace('3:','')
				physics = physics.split('\n')
				print(physics[0])
				car_data = physics[0].split(',')
				print (car_data)
				print('')
				print (car_data[23])
				tire_friction=car_data[23].split('=')
				tire_friction=tire_friction[2]
				print(tire_friction)
				if (float(tire_friction)==1.5):
					client.send(("Tire friction is 1.5").encode())

except KeyboardInterrupt:
	sys.exit(0)

		

q

client.close()


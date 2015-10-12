import getmedia

while True:
	try:	
		getmedia.run_loop()
	except KeyboardInterrupt:
		break
	except:
		pass

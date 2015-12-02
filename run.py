#!/usr/bin/python
import getmedia
import traceback

while True:
	try:	
		getmedia.run_loop()
	except KeyboardInterrupt:
		break
	except:
		print "Exception occured"
		traceback.print_exc()
		pass

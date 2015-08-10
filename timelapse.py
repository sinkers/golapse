from goprohero import GoProHero
import requests
import time
import re

# Enter the password for your gopro and make sure you are connected to the wifi network
PASSWORD = ""
SLEEP_TIME = 360
MAX_ERRORS = 10

CAMERA_ON = "http://10.5.5.9/bacpac/PW?t={}&p=%01"

camera = GoProHero(password=PASSWORD)
error_count = 0

def run_command(url):
	resp = requests.get(url.format(PASSWORD))
	if resp.status_code != 200:
		print "Error turning on. Status code: %s" % resp.status_code
		error_count += 1
		if error_count > MAX_ERRORS:
			print "Too many errors exiting"
			# Raise some kind of alert
			return False
	else:	
		error_count = 0
		return True

while True:
	#camera on
	if not run_command(CAMERA_ON):
		break

	# Wait for camera to turn on
	print "Waiting to power on"
	time.sleep(5)
	# Turn on camera mode
	resp = requests.get("http://10.5.5.9/camera/CM?t={}&p=%01".format(PASSWORD))
	time.sleep(1)
	# Set camera resolution
	resp = requests.get("http://10.5.5.9/camera/PR?t={}&p=%00".format(PASSWORD))
	time.sleep(1)
	# Take a photo
	print "Taking photo"
	resp = requests.get("http://10.5.5.9/camera/SH?t={}&p=%01".format(PASSWORD))

	resp = requests.get("http://10.5.5.9:8080/videos/DCIM/")
	dir_list = resp.text.split()
	last_dir = False
	for line in dir_list:
		#print line
		search_obj = re.search( r'[0-9][0-9][0-9]GOPRO', line, re.M|re.I)
		if search_obj:
			last_dir = search_obj.group()
	if last_dir:
		resp = requests.get("http://10.5.5.9:8080/videos/DCIM/{}".format(last_dir))
		dir_list = resp.text.split()
		for line in dir_list:
			#print line
			search_obj = re.search( r'GOPR[0-9][0-9][0-9][0-9]', line, re.M|re.I)
			if search_obj:
				print search_obj.group()
	# camera off
	time.sleep(2)
	print "Powering off"
	resp = requests.get("http://10.5.5.9/bacpac/PW?t={}&p=%00".format(PASSWORD))
	print "Sleep for {} seconds\n".format(SLEEP_TIME)
	time.sleep(SLEEP_TIME)
	


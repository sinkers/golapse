import requests
import time
import re
from wireless import Wireless

LOCAL_DIR = "/Users/asinclair/Pictures"

def get_media_dirs():
	resp = requests.get("http://10.5.5.9:8080/videos/DCIM/")
	time.sleep(10)
	dir_list = resp.text.split()

	media_dirs = []
	for line in dir_list:
		#print line
		search_obj = re.search( r'[0-9][0-9][0-9]GOPRO', line, re.M|re.I)
		if search_obj:
			media_dirs.append(search_obj.group())
	return media_dirs

def get_media(dir_list):
	for item in dir_list:
		print "Processing directory {}".format(item)
		resp = requests.get("http://10.5.5.9:8080/videos/DCIM/{}".format(item))
		if resp.status_code == 200:
			dir_list = resp.text.split()
			for line in dir_list:
				last_photo = False
				search_obj = re.search( r'GOPR[0-9][0-9][0-9][0-9].JPG', line, re.M|re.I)
				if search_obj:
					last_photo = search_obj.group()
				# Fix shit logic
				search_obj = re.search( r'G[0-9][0-9][0-9][0-9][0-9][0-9][0-9].JPG', line, re.M|re.I)
				if search_obj:
					last_photo = search_obj.group()
				if last_photo:
					print "http://10.5.5.9:8080/videos/DCIM/{}/{}".format(item, last_photo)
					resp = requests.get("http://10.5.5.9:8080/videos/DCIM/{}/{}".format(item, last_photo), stream=True)
					print resp.status_code
					print resp.headers["last-modified"]
					t = time.strftime("%Y%m%d-%H%M%S", time.strptime(resp.headers["last-modified"], "%a, %d %b %Y %H:%M:%S %Z"))
					if resp.status_code == 200:
						path = "{}/{}.JPG".format(LOCAL_DIR, t)
						print "Writing to {}".format(path)
						with open(path, 'wb') as f:
							for chunk in resp:
								f.write(chunk)



get_media(get_media_dirs())
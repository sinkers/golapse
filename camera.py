import requests
import time
import re
from wireless import Wireless

# Enter the password for your gopro and make sure you are connected to the wifi network
PASSWORD = ""
GOPRO_NETWORK = "as-gopro"
UPLOAD_NETWORK = "Nifi"
SLEEP_TIME = 360
MAX_ERRORS = 10
LOCAL_DIR = "/Users/andrew/Pictures/"

CAMERA_ON = "http://10.5.5.9/bacpac/PW?t={}&p=%01"
DELETE_LAST_PHOTO = "http://10.5.5.9/camera/DL?t={}"
CAMERA_PHOTO_MODE_ON = "http://10.5.5.9/camera/CM?t={}&p=%01"
CAMERA_RESOLUTION_MEDIUM = "http://10.5.5.9/camera/PR?t={}&p=%06"

wireless = Wireless()

error_count = 0


def run_command(url):
    global error_count
    try:
        resp = requests.get(url.format(PASSWORD))
        if resp.status_code != 200:
            print "Error processing command %s. Status code: %s" % (url, resp.status_code)
            error_count += 1
            if error_count > MAX_ERRORS:
                print "Too many errors exiting"
                # Raise some kind of alert
                return False
        else:
            error_count = 0
            return True
    except:
        print "Network exception. Error opening url %s" % url
        return False


while True:
    wireless.connect(ssid=GOPRO_NETWORK, password=PASSWORD)
    # camera on
    if not run_command(CAMERA_ON):
        wireless.connect(ssid=UPLOAD_NETWORK, password=PASSWORD)
        break

    # Wait for camera to turn on
    print "Waiting to power on"
    time.sleep(5)
    # Turn on camera mode
    run_command(CAMERA_PHOTO_MODE_ON)
    time.sleep(1)
    # Set camera resolution to medium
    run_command(CAMERA_RESOLUTION_MEDIUM)
    time.sleep(1)
    # Take a photo
    print "Taking photo"
    run_command("http://10.5.5.9/camera/SH?t={}&p=%01")

    resp = requests.get("http://10.5.5.9:8080/videos/DCIM/")
    print "Wait for photo to write"
    time.sleep(10)
    dir_list = resp.text.split()
    last_dir = False
    last_photo = False
    for line in dir_list:
        #print line
        search_obj = re.search(r'[0-9][0-9][0-9]GOPRO', line, re.M | re.I)
        if search_obj:
            last_dir = search_obj.group()
    if last_dir:
        resp = requests.get("http://10.5.5.9:8080/videos/DCIM/{}".format(last_dir))
        if resp.status_code == 200:
            dir_list = resp.text.split()
            for line in dir_list:
                #print line
                search_obj = re.search(r'GOPR[0-9][0-9][0-9][0-9]', line, re.M | re.I)
                if search_obj:
                    last_photo = search_obj.group()
    else:
        print "Error getting photo list"
    if last_photo:
        iso_time = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
        print "http://10.5.5.9:8080/videos/DCIM/{}/{}.JPG".format(last_dir, last_photo)
        resp = requests.get("http://10.5.5.9:8080/videos/DCIM/{}/{}.JPG".format(last_dir, last_photo), stream=True)
        print resp.status_code
        if resp.status_code == 200:
            path = "{}/{}.JPG".format(LOCAL_DIR, iso_time)
            print "Writing to {}".format(path)
            with open(path, 'wb') as f:
                for chunk in resp:
                    f.write(chunk)

        run_command(DELETE_LAST_PHOTO)
    # camera off
    time.sleep(2)
    print "Powering off"
    resp = requests.get("http://10.5.5.9/bacpac/PW?t={}&p=%00".format(PASSWORD))

    wireless.connect(ssid=UPLOAD_NETWORK, password=PASSWORD)

    print "Sleep for {} seconds\n".format(SLEEP_TIME)
    time.sleep(SLEEP_TIME)
	


import requests
import time
import re
import subprocess
from boto.s3.connection import S3Connection
from boto.s3.key import Key
import os
import shutil
import exifread
import threading
import goprohero
import ConfigParser
import sendgrid

config = ConfigParser.ConfigParser()
config.readfp(open('config.cfg'))

LOCAL_DIR = config.get("config","local_dir")
TMP_DIR = config.get("config","tmp_dir")
BLACK_THRESHOLD = config.getfloat("config","black_threshold")
CONVERT = config.get("config","convert_program")
BUCKET = config.get("config","s3_bucket")
AWS_KEY = config.get("config","aws_key")
AWS_SECRET = config.get("config","aws_secret")
GP_PASSWORD = config.get("config","gopro_password")
REGION = config.get("config","aws_region")
BASE_DEST = config.get("config","base_dest_dir")
SLEEP_TIME = config.getfloat("config","sleep_time")
ALERT_EMAIL = config.get("config","alert_email")
SENDGRID_USER = config.get("config","sendgrid_user")
SENDGRID_KEY = config.get("config","sendgrid_key")
MAX_ERRORS = config.getint("config","max_errors")

# Used for tracking consecutive errors
error_count = 0

def run_command(option, cmd, holdoff=0):
    global error_count
    time.sleep(holdoff)
    print "%s %s" % (error_count, MAX_ERRORS)
    if error_count > MAX_ERRORS:
        print "Too many errors exiting"
        send_email("Uh oh too many errors running camera commands. Camera not responding")
        error_count = 0
        return False
        # Raise some kind of alert
    
    camera = goprohero.GoProHero()
    camera.password(GP_PASSWORD)
    try:
        result = camera.command(option, cmd)
        if result == False:
            print "Error processing command was False %s %s" % (option, cmd)
            error_count += 1
            run_command(option, cmd, error_count*10)
        else:
            error_count = 0
            return True
    except:
        print "Error processing command exception %s %s" % (option, cmd)
        error_count += 1
        run_command(option, cmd, error_count*10)

def send_email(message_txt):
    sg = sendgrid.SendGridClient(SENDGRID_USER, SENDGRID_KEY)
    message = sendgrid.Mail()
    message.add_to(ALERT_EMAIL)
    message.set_from(SENDGRID_USER)
    message.set_subject("GoLapse Alert")
    message.set_html(message_txt)
    sg.send(message)
    return True

def s3_upload(file_name, key):
    # Creates a new file with just the file name at root of bucket
    conn = S3Connection(AWS_KEY, AWS_SECRET, host=REGION)
    bucket = conn.get_bucket(BUCKET)
    k = Key(bucket)
    # create a key for the new file
    k.key = key
    # upload the file
    k.set_contents_from_filename(file_name)
    # make it public read only
    k.set_acl('public-read')
    #only return the url part as we have made it public
    url = k.generate_url(0,'GET',force_http=True)
    return url.split('?')[0]

def local_copy(local_img, new_img, base_dir):
    p = os.path.join(base_dir, os.path.dirname(new_img))
    try:
        os.makedirs(p)
    except:
        pass
        #print "Couldn't create dir {} probably already exists".format(p)
    print "Copying {} to {}".format(local_img, os.path.join(p, os.path.basename(new_img)))
    shutil.copy2(local_img, os.path.join(p, os.path.basename(new_img)))

def get_created_path(img):
    f = open(img)
    tags = exifread.process_file(f, details=False)
    dt = time.strptime(str(tags["EXIF DateTimeOriginal"]).split("=")[0],"%Y:%m:%d %H:%M:%S")
    return time.strftime('%Y/%m/%d/%H/%M%S.JPG', dt)
    #file_part = datetime.datetime.fromtimestamp(os.path.getctime(img)).strftime('%M%S')
    #return path_part, file_part

def img_black(img):
    #Detect if an image is all black
    cmd = [CONVERT, img, '-format', '"%[mean]"', 'info:']
    try:
        # Note the output from convert may vary a bit, TODO add regex
        result = float(subprocess.check_output(cmd)[1:-2])
        if result < BLACK_THRESHOLD:
            return True
        else:
            return False
    except:
        print "error getting threshold from convert"
        return False


def get_media_dirs():
    resp = requests.get("http://10.5.5.9:8080/videos/DCIM/")
    time.sleep(10)
    dir_list = resp.text.split()

    media_dirs = []
    for line in dir_list:
        # print line
        search_obj = re.search(r'[0-9][0-9][0-9]GOPRO', line, re.M | re.I)
        if search_obj:
            media_dirs.append(search_obj.group())
    return media_dirs

def process_images(imgs, base_dir, d):
     for i in imgs:
        if not img_black(os.path.join(base_dir, d, i)):
            new_path = get_created_path(os.path.join(base_dir, d, i))
            local_copy(os.path.join(base_dir, d, i), new_path, BASE_DEST)
        else:
            print "Too much black {}".format(os.path.join(base_dir, d, i))


def get_media_filesystem(base_dir):
    dirlist = os.listdir(base_dir)
    dirs = []
    for d in dirlist:
        if os.path.isdir(os.path.join(base_dir, d )) and d[-5:] == "GOPRO":
            dirs.append(d)

    threads = []
    for d in dirs:
        if os.path.isdir(os.path.join(base_dir, d )):
            imgs = os.listdir(os.path.join(base_dir, d))
            t = threading.Thread(target=process_images, args=(imgs, base_dir, d))
            threads.append(t)
            t.start()
            #process_images(imgs, base_dir, d)

def images_left():
    camera = goprohero.GoProHero()
    camera.password(GP_PASSWORD)
    try:
        status = camera.status()
        if status["npics"] > 0:
            return status["npics"]
        else:
            return 0
    except:
        # Only return False if we are sure
        print "Error getting status"
        return -1


def upload_latest():
    # Just uploads the last tmpfile
    tmpfile = os.path.join(TMP_DIR, "tmpfile.jpg")
    if not img_black(tmpfile):
        target_key = "latest.jpg"
        print "Uploading latest to S3"
        t = threading.Thread(target=s3_upload, args=(tmpfile, target_key))
        t.start()


def delete_all():
    camera = goprohero.GoProHero()
    camera.password(GP_PASSWORD)
    camera.command("delete_all")



def get_media(dir_list):
    for item in dir_list:
        print "Processing directory {}".format(item)
        resp = requests.get("http://10.5.5.9:8080/videos/DCIM/{}".format(item))
        if resp.status_code == 200:
            dir_list = resp.text.split()
            for line in dir_list:
                last_photo = False
                search_obj = re.search(r'GOPR[0-9][0-9][0-9][0-9].JPG', line, re.M | re.I)
                if search_obj:
                    last_photo = search_obj.group()
                # Fix shit logic
                search_obj = re.search(r'G[0-9][0-9][0-9][0-9][0-9][0-9][0-9].JPG', line, re.M | re.I)
                if search_obj:
                    last_photo = search_obj.group()
                if last_photo:
                    print "Getting image http://10.5.5.9:8080/videos/DCIM/{}/{}".format(item, last_photo)
                    resp = requests.get("http://10.5.5.9:8080/videos/DCIM/{}/{}".format(item, last_photo), stream=True)
                    print resp.status_code

                    if resp.status_code == 200:

                        tmp_path = os.path.join(TMP_DIR, "tmpfile.jpg")
                        print "Writing to {}".format(tmp_path)
                        #Write to temp file
                        with open(tmp_path, 'wb') as f:
                            for chunk in resp:
                                f.write(chunk)
                        f.close()
                        # Delete image if black
                        if img_black(tmp_path):
                            print ("Image too black")
                        else:
                            t = get_created_path(tmp_path)
                            path = os.path.join(LOCAL_DIR, t)
                            p = os.path.join(LOCAL_DIR, os.path.dirname(path))
                            try:
                                os.makedirs(p)
                                # Note tmpfile just gets written over on the next one
                            except:
                                pass
                            print "Copy to {}".format(path)
                            shutil.copy2(tmp_path, path)


def run_loop():
    while True:
        run_command("record", "on")
        # Need to wait before photo is on disk
        time.sleep(SLEEP_TIME)
        run_command("record", "off")
        get_media(get_media_dirs())
        print images_left()
        upload_latest()
        run_command("delete_all","")
        # Just a little extra wait for delete to finish as may take some time depending on size and how full
        # card was
        time.sleep(5)


#get_media(get_media_dirs())
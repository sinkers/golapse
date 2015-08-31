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

LOCAL_DIR = "/Users/andrew/Pictures"
TMP_DIR = "/tmp"
BLACK_THRESHOLD = 1000.0
CONVERT = "convert"
BUCKET = "timelapse.capebernier.com.au"
AWS_KEY = ""
AWS_SECRET = ""
REGION = "s3-ap-southeast-2.amazonaws.com"
BASE_DEST = "/Volumes/Data/Photos/CBVTimelapse/"

def hello():
    print "hello"

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
        if os.path.isdir(os.path.join(base_dir, d )):
            dirs.append(d)

    threads = []
    for d in dirs:
        if os.path.isdir(os.path.join(base_dir, d )):
            imgs = os.listdir(os.path.join(base_dir, d))
            t = threading.Thread(target=process_images, args=(imgs, base_dir, d))
            threads.append(t)
            t.start()
            #process_images(imgs, base_dir, d)



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
                    print "http://10.5.5.9:8080/videos/DCIM/{}/{}".format(item, last_photo)
                    resp = requests.get("http://10.5.5.9:8080/videos/DCIM/{}/{}".format(item, last_photo), stream=True)
                    print resp.status_code
                    print resp.headers["last-modified"]
                    t = time.strftime("%Y/%m/%d/%H/%M%S.JPG",
                                      time.strptime(resp.headers["last-modified"], "%a, %d %b %Y %H:%M:%S %Z"))
                    if resp.status_code == 200:
                        path = "{}/{}".format(LOCAL_DIR, t)
                        tmp_path = "{}/tmpfile.jpg"
                        print "Writing to {}".format(tmp_path)
                        #Write to temp file
                        with open(tmp_path, 'wb') as f:
                            for chunk in resp:
                                f.write(chunk)
                        f.close()
                        # Delete image if black
                        if img_black(tmp_path):
                            print ("Too black, deleting {}".format(path))
                        else:
                            p = os.path.join(LOCAL_DIR, os.path.dirname(path))
                            try:
                                os.makedirs(p)
                                print "Copy to {}".format(path)
                                shutil.copy2(tmp_path, path)
                                # Note tmpfile just gets written over on the next one
                            except:
                                pass


#get_media(get_media_dirs())
#import uuid
import time
import os, sys
import re
import boto
import redis
from flask import Flask, render_template, redirect, request, url_for, make_response
from werkzeug import secure_filename
# from PIL import Image, ImageOps
# import hashlib
import json
import reference as ref

if 'VCAP_SERVICES' in os.environ:
    VCAP_SERVICES = json.loads(os.environ['VCAP_SERVICES'])
    CREDENTIALS = VCAP_SERVICES["rediscloud"][0]["credentials"]
    r = redis.Redis(host=CREDENTIALS["hostname"], port=CREDENTIALS["port"], password=CREDENTIALS["password"])
    print "Now running in PCF"
else:
    r = redis.Redis(host='redis-13396.c54.ap-northeast-1-2.ec2.cloud.redislabs.com', port='13396', password='HQpnL0R80nKF8CH8O5FuW0dljx750APv')
    print "Now running in local system"

##bname = os.environ['bucket']
##ecs_access_key_id = os.environ['ECS_access_key']
##ecs_secret_key = os.environ['ECS_secret']
##ecs_host = os.environ['ECS_host']
##access_url = os.environ['object_access_URL']

size = 150, 150
epoch_offset = 0 #The offset in seconds with Bangkok

#boto.set_stream_logger('boto')

#####  ECS version  #####
session = boto.connect_s3(aws_access_key_id=ref.ecs_access_key_id, \
                          aws_secret_access_key=ref.ecs_secret_key, \
                          host=ref.ecs_host)

#####  AWS S3 version  #####
##session = boto.connect_s3(ecs_access_key_id, ecs_secret_key)

b = session.get_bucket(bname)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/'
app.config['ALLOWED_EXTENSIONS'] = set(['mp3', 'MP3', 'mp4', 'MP4'])

@app.route('/')
def menu():
    global stimes
    global r
    r.incr('hitcounter')
    photocount = r.get("pcounter")
    print "Amount of added music :", musiccount
    reviewcount = r.get("rcounter")
    print "Amount of reviews : ", reviewcount

    current = int(time.time())-time.timezone
    print current
    anchor = 0
    for t in stimes:
        if current > int(t):
            anchor = t

    print "Anchor is " + str(anchor)

    uuid = request.cookies.get('uuid')
    if not uuid:
        print "uuid cookie was not present"
        uuid = r.incr('ucounter')
    print "uuid now is :", uuid
    usercount = r.get('ucounter')
    print "User counter : ", usercount
    resp = make_response(render_template('main_menu.html', anchor=anchor, reviews=reviewcount, musics=musiccount, ucount=usercount))
    resp.set_cookie('uuid',str(uuid), max_age=604800)
    return resp

### Read stations list
def rstations():
   readurl = str("https://" + reference.access_url + "/" + reference.bname + "/" + "stationslist.txt")
   print (readurl)                # should delete
   st = requests.get(readurl)
   if (st.status_code == 200):
      print "SUCCESSFUL to GET CMD\n"
   else:
      print "read error@rcmd() as code =" + str(st.status_code)
   return [st.status_code, st.text]


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

@app.route('/upload_music.html')
def index():
    global r
    r.incr('hitcounter')
    return render_template('upload_music.html')


@app.route('/upload', methods=['POST'])
def upload():
    global size
    global b
    global r

    file = request.files['file']
    if file and allowed_file(file.filename):
        # Make the filename safe, remove unsupported chars
        filename = secure_filename(file.filename)
        print "am here"
        justname = filename.rsplit(".",1)[0]
        justname = justname + str (int (time.time() * 1000))
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        print "Uploading " + filename + " as key " + justname
        k = b.new_key(justname)
        k.set_contents_from_filename(filename)
        k.set_acl('public-read')

        os.remove(filename)

        uuid = request.cookies.get('uuid')
        Counter = r.incr('pcounter')
        print "the music counter is now: ", Counter
        newmusic = 'music' + str(Counter)
        print "Lets create Redis hash: " , newmusic
        r.hmset(newmusic,{'name':justname, 'uuid':uuid})
        return"""
        <html>
          <head>
            <link rel=stylesheet type=text/css href="/static/style.css">
            <meta name="viewport" content="width=410, initial-scale=0.90">
          </head>
          <body>
            <div class="container">
            <div class="content">
            <h3>Thank You!</h3>
            <h4>You have just uploaded a Music to: <br><a href="https://portal.ecstestdrive.com/">ECS Object Storage</a></h4>
            <a href="/"><h3>Back to main menu</h3></a>
        <img src="/static/logo.png" width="270" />
	"""

@app.route('/showmusics.html')
def musics():
    global r
    global bname
    r.incr('hitcounter')
    musiccount = r.get("pcounter")

    for each_photo in r.keys('music*'):
        print each_music
        musicfiles = "<input type="checkbox" name=musicfiles value=r.hget(each_music,'name')>r.hget(each_music,'name')"

    f = rstations()
    slist = json.loads (f[1])
    for each_station in slist['stations']['station']
       musicstations = "<option value=" + slist['stations']['link'][each_station] + ">"+ slist['stations']['station'][each_station] + "</option>"

    pagepart1 = """
	<html>
	  <head>
	    <link rel=stylesheet type=text/css href="static/style.css">
	    <meta name="viewport" content="width=410, initial-scale=0.90">

	  </head>
	  <body>
	     <div class="container">
	     <div class="content">
	     <img src="static/logo.png" width="270" />
	     <h2>Total musics uploaded: {} </h2>
	     <a href="/"><h3>Back to main menu</h3></a>
	     <form action="setplaylist" method="post">
	        <body style="background-color: grey;">
    """.format(musiccount)

    pagepart2 = """
	        </body>
	        <br><br>
	        <h2>STATIONS LIST</h2>
	        <h4>picked up from shoutcast.com</h4>
	        <body style="backgroune-color: grey;">
	            <select name="selectedstation" size="4">
    """

    pagepart3 = """
	            </select>
	            <br><br>
		    <input class="btn-blue" type="submit" value="SET PLAYLIST">
		    <br>
	        </body>
	     </form>
	  </body>
	</html>
    """

    filetable = pagepart1 + musicfiles + pagepart2 + musicstations + pagepart3
    return filetable

@app.route('/setplaylist', methods=['POST'])
def setplaylist():
    mf = musicfiles
    ss = selectedstation
    text = []

    for each_file in mf:
       text = text + mf[each_file] + "\n"

    text = text + ss + "\n"

    key = b.new_key ('playlist.txt')
    key.set_contents_from_string(text)
    key.set_acl('public-read')


#################################################################
## Two ways of accessing objects in ECS
## http://bucketname.namespace.public.ecstestdrive.com/objectname
## or
## http://namespace.public.ecstestdrive.com/bucketname/objectname
## We are using the second one so that you change only an env var
## to switch between AWS and ECS

@app.route('/aboutus')
def aboutus():
    global r
    r.incr('hitcounter')
    resp = make_response(render_template('aboutus.html'))
    return resp

##########################################
# This section contains hidden admin links

##@app.route('/kdump')
##def kdump():
##    global session
##    print session.get_all_buckets()
##    for bucket in session.get_all_buckets():
##        print "In bucket: " + bucket.name
##        for object in bucket.list():
##            print(object.key)
##    return "Keys have been dumped in the console"

@app.route('/rdump')
def rdump():
    global r
    output = "session; content; presenter; uuid<br>"
    for each_review in r.keys('review*'):
        output = output + "%s; %s; %s; %s<br>" % (r.hget(each_review,'session'), \
                                              r.hget(each_review,'content'), \
                                              r.hget(each_review,'presenter'), \
                                              r.hget(each_review,'uuid'))

    return output

@app.route('/pdump')
def pdump():
    global r
    output = "photo, uuid<br>"
    for each_photo in r.keys('photo*'):
        output = output + "%s, %s<br>" % (r.hget(each_photo,'name'), \
                                              r.hget(each_photo,'uuid'))

@app.route('/sdump')
def sdump():
    global r

    output = ""
    for each_survey in r.keys('survey*'):
        output += "%s<br>" % (r.hget(each_survey,'review_string'))

    return output


@app.route('/stats')
def hitdump():
    global r
    hits = r.get('hitcounter')
    visitors = r.get('ucounter')
    reviews = len(r.keys('review*'))
    surveys = len(r.keys('survey*'))
    resp = "Total pageviews: " + str(hits) + "<br>Unique visitors: " + str(visitors) + "<br>Total reviews: " \
           + str(reviews) + "<br>Surveys received: " + str(surveys)
    return resp



@app.route('/uid')
def uid():
    uuid = request.cookies.get('uuid')
    return "Your user ID is : " + uuid

if __name__ == "__main__":
	app.run(debug=False, host='0.0.0.0', \
                port=int(os.getenv('PORT', '5000')), threaded=True)

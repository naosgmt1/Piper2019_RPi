#!/usr/bin/env python3
# coding: utf-8

### IMPORT ###
import uuid
import time
import datetime
import os
import sys
import boto
import redis
import json
import requests
import reference as ref
from flask import Flask, render_template, redirect, request, Response, make_response
import werkzeug

### PARAMETER ###
dtnow = datetime.datetime.now()
print (dtnow)

    #### ECS version ####
session = boto.connect_s3(aws_access_key_id=ref.ecs_access_key_id, \
                          aws_secret_access_key=ref.ecs_secret_key, \
                          host=ref.ecs_host)
b = session.get_bucket(ref.bname)

if ('VCAP_SERVICES' in os.environ):
    VCAP = json.loads(os.environ['VCAP_SERVICES'])
    CREDENTIALS = VCAP["rediscloud"][0]["credentials"]
    r = redis.Redis(host=CREDENTIALS["hostname"], port=CREDENTIALS["port"], password=CREDENTIALS["password"])
    print ("Now running in PCF")
else:
    print ("ERROR in VCAP_SERVICES", end=": ")
    print (VCAP)

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = set(['mp3', 'MP3', 'mp4', 'MP4'])

def allowed_file(filename):
    return ('.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS'])

### Read stations list
def rstations():

   readurl = str ("https://" + ref.access_url + "/" + ref.bname + "/" + "stationslist.txt")
   st = requests.get(readurl)
   if (st.status_code == 200):
      print ("SUCCESSFUL to GET CMD\n")
   else:
      print ("read error@rcmd() as code =" + str(st.status_code))
   f = [st.status_code, st.text]
   return f

### Read cmdlist
def rcmd():
   readurl = str("https://" + ref.access_url + "/" + ref.bname + "/" + "cmdlist.txt")
   r = requests.get(readurl)
   if (r.status_code == 200):
      print ("SUCCESSFUL to GET CMD\n")
   else:
      print ("read error@rcmd() as code =" + str(r.status_code))
   return [r.status_code, r.text]

### MAIN PAGE ###
@app.route('/')
def menu():
    global r
    if not r.get("ucounter"):
        r.set("ucounter","0")
    r.incr('hitcounter')
    musiccount = str(r.get('pcounter'), encoding='utf-8')
    usercount = str(r.get('ucounter'), encoding='utf-8')
    uuid = request.cookies.get('uuid')
    if not uuid:
        print ("uuid cookie was not present")
        uuid = r.incr('ucounter')

    resp = "Hello Music!"

    print ("resp is ", end=": ")
    print (resp)
    print ("uuid now is : ")
    print (uuid)

    usercount = str(r.get('ucounter'), encoding='utf-8')
    print ("User counter : ")
    print (usercount)

    resp = make_response (render_template('mainmenu.html', musiccnt=musiccount, ucount=usercount))
    resp.set_cookie('uuid', str(uuid), max_age=604800)

    print ("RETURNING MAIN PAGE")

    return resp

@app.route('/upload_music.html')
def index():
    global r
    r.incr('hitcounter')
    print ("Now, upload_music.html")
    return render_template('upload_music.html')

@app.route('/upload', methods=['POST'])
def upload():
    global size
    global b
    global r

    rfile = request.files['file']
    print (rfile.filename)
    if rfile and allowed_file(rfile.filename):
        # Make the filename safe, remove unsupported chars
        savename = werkzeug.utils.secure_filename(rfile.filename)
        print (savename)
        print ("am here")
### Use just name in case of unique name is required while same name files are uploaded.
#        justname = savename.rsplit(".",1)[0]
#        justname = justname + str (int (time.time() * 1000))
#        print (justname)
        rfile.save(os.path.join(app.config['UPLOAD_FOLDER'], savename))

        print ("Uploading " + savename + " as key " + justname)
        k = b.new_key(savename)
        k.set_contents_from_filename(app.config['UPLOAD_FOLDER'] + savename)
        k.set_acl('public-read')

        os.remove(app.config['UPLOAD_FOLDER'] + savename)

        uuid = request.cookies.get('uuid')
        Counter = r.incr('pcounter')
        print ("the music counter is now: ")
        print (Counter)
        newmusic = 'music' + str(Counter)
        print ("Lets create Redis hash: ")
        print (newmusic)
        r.hmset(newmusic,{'name':savename, 'uuid':uuid})
        return"""
        <html>
          <head>
            <link rel=stylesheet type=text/css href="/static/style.css">
            <meta name="viewport" content="width=410, initial-scale=0.90">
            <meta http-equiv="Refresh" content="15;URL=/">
          </head>
          <body>
            <div class="container">
            <div class="content">
            <h2>Thank You!</h2>
            <h3>You have just uploaded a Music to: <br><a href="https://portal.ecstestdrive.com/">ECS Object Storage</a></h3>
            <h3><a href="/">Back to main menu</a></h3>
        <img src="/static/logo.png" width="270" />
        """
    else: 
        return "ERROR in UPLOADING FILE WAS FOUND"

@app.route('/showmusics')
def musics():
    global r
    global bname
    r.incr('hitcounter')
    musiccount = str(r.get("pcounter"), encoding='utf-8')
    musicfiles = "<div><label><input type=\"checkbox\" name=\"NO SELECT\" value=\"\"/></label></div>"

    for each_music in r.keys('music*'):
        print (each_music)
        decfilen = str(r.hget(each_music,'name'), encoding='utf-8')
        print (decfilen)
        musicfiles = musicfiles + "<div><label><input type=\"checkbox\" name=\"musicfiles\" value=\"" \
                   + decfilen \
                   + "\"/>" \
                   + decfilen \
                   + "</label></div>"
    print ("musicfiles", end=": ")
    print (musicfiles)
    f = rstations()
    print("===Kicked rstatinos=== with",end=":")
    print(f)
    slist = json.loads (f[1])
    musicstations = ""
    for each_station in slist['stations']:
        musicstations = musicstations + "<option value=" \
                      + each_station['link'] \
                      + ">" \
                      + each_station['station'] \
                      + "</option>"

    pagepart1 = """
	<html>
	  <head>
	    <link rel=stylesheet type=text/css href=\"static/style.css\">
	    <meta name=\"viewport\" content="width=410, initial-scale=0.90">

	  </head>
	  <body>
	     <div class=\"container\">
	     <div class=\"content\">
	     <img src=\"static/logo.png\" width=\"270\" />
	     <h2>Total musics uploaded: {{ musiccount }} </h2>
	     <a href=\"/\"><h3>Back to main menu</h3></a>
	     <form action=\"setplaylist\" method=\"post\">
	        <body style=\"background-color: grey;\">
    """.format(musiccount)

    pagepart2 = """
	        </body>
	        <br><br>
	        <h2>STATIONS LIST</h2>
	        <h4>picked up from shoutcast.com</h4>
	        <body style=\"backgroune-color: grey;\">
	            <select name=\"selectedstation\" size=\"4\">
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
    global b
    mf = request.form.getlist("musicfiles")       # musicfiles
    ss = request.form.get("selectedstation")      # selectedstation
    text = ""
    dlfiles = ""
    musiccount = str(r.get('pcounter'), encoding='utf-8')
    usercount = str(r.get('ucounter'), encoding='utf-8')

    print("mf", end=" = ")
    print(mf)
    print("ss", end=" = ")
    print(ss)

    for each_file in mf:
       print ("each file", end=": ")
       print (each_file)
       text = text + "https://" + ref.access_url + "/" + ref.bname + "/" + each_file + "\n"
       dlfiles = dlfiles + each_file + "\n"

    text = text + ss + "\n"

    print("playlist is",end=" : ")
    print(text)
    print(type(text))

    key = b.new_key ('playlist.txt')
    key.set_contents_from_string(text)
    key.set_acl('public-read')

    resp = "Thanks! just set playlist.txt, now \n" + dlfiles + "\n" + ss + "\n"
    response = make_response (render_template('playbutton_now.html', resp=resp, musiccnt=musiccount, ucount=usercount))

    return response


@app.route('/playbutton')
def playbutton():
    global dtnow
    global b
    musiccount = str(r.get('pcounter'), encoding='utf-8')
    usercount = str(r.get('ucounter'), encoding='utf-8')
    uuid = request.cookies.get('uuid')
    if not uuid:
        print ("uuid cookie was not present")
        uuid = r.incr('ucounter')

    dtnow = datetime.datetime.now()

    f = rcmd()
    cmdlist = json.loads (f[1])
    print (cmdlist)              # should delete
    print (cmdlist['kicked date']) # should delete
    print (cmdlist['operation']) # should delete

    if (cmdlist['kicked date'] == "1980/01/01 00:00:01"):
       resp = "PREVIOUS COMMAND HAS NOT BEEN FINISHED"
    else:
       cmdlist['kicked date'] = "1980/01/01 00:00:01"
       cmdlist['entry date'] = "{0:%Y/%m/%d %H:%M:%S}".format(dtnow)
       if (cmdlist['operation'] == "stop"):
           cmdlist['operation'] = "play"
           cmdop = "play"
       else: 
           cmdlist['operation'] = "stop"
           cmdop = "stop"

       key = b.new_key ('cmdlist.txt')
       key.set_contents_from_string(json.dumps(cmdlist))
       key.set_acl('public-read')
       resp = "SUCCESS to SET OPERATION \n as " + cmdop
    print ("playbutton", end=": ")
    print (resp)

    response = make_response (render_template('playbutton_now.html', resp=resp, musiccnt=musiccount, ucount=usercount))

    return response

@app.route('/aboutus')
def aboutus():
    global r
    r.incr('hitcounter')
    resp = make_response(render_template('aboutus.html'))
    print (resp)
    return resp


if __name__ == "__main__":
	app.run(debug=False, host='0.0.0.0', \
                port=int(os.getenv('PORT', '5000')), threaded=True)



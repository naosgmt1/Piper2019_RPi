#!/usr/bin/env python3

import os
import time
import requests
import subprocess
import json
import boto
import datetime

### PERSONAL PARAMETERS
import reference

### DECLARE of PARAMS
f = []
dtnow = datetime.datetime.now()
print (dtnow)

### S3 access to ECS/TESTDRIVE 
session = boto.connect_s3 (aws_access_key_id=reference.ecs_access_key_id, \
                           aws_secret_access_key=reference.ecs_secret_key, \
                           host=reference.ecs_host)
b = session.get_bucket(reference.bname)
print ("Bucket is " + str (b))   # should delete
print ("in ECS connection - " + str (session))  # should delete

### Fetch to playlist.txt
def openPlaylist():
   global r
   readurl = str("https://" + reference.access_url + "/" + reference.bname + "/" + "playlist.txt")
   r = requests.get(readurl)

   if (r.status_code == 200): 
      print ("SUCCESSFUL to GET&READ\n")
   else:
      print ("read error as code =" + r.status_code)
   return [r.status_code, r.text] 

### Play vlc 
def playvlc(plist):
   print ("### start playvlc ###\n")  # should delete
   cmdlist = ["vlc"]
   cmdlist.extend (plist.splitlines())
   print (cmdlist)
   return (subprocess.Popen (cmdlist, stderr=subprocess.PIPE, stdout=subprocess.PIPE))

### Stop vlc
def stopvlc():
   print ("### start stopvlc ###\n")  # should delete
   cmdlist = ["killall", "vlc"]
   print (cmdlist)
   return (subprocess.Popen (cmdlist, stderr=subprocess.PIPE, stdout=subprocess.PIPE))

### Read cmdlist
def rcmd():
   readurl = str("https://" + reference.access_url + "/" + reference.bname + "/" + "cmdlist.txt")
   print (readurl)                # should delete
   r = requests.get(readurl)
   if (r.status_code == 200):
      print ("SUCCESSFUL to GET CMD\n")
   else:
      print ("read error@rcmd() as code =" + str(r.status_code))
   return [r.status_code, r.text]

### Main Routine ###
if __name__ == "__main__":
   while (True):
       f = rcmd()
       cmdlist = json.loads (f[1])
       print (cmdlist)              # should delete
       print (cmdlist['kicked date']) # should delete
       print (cmdlist['operation']) # should delete

       if (cmdlist['kicked date'] == "1980/01/01 00:00:01"):
          cmdlist['kicked date'] = "2020/01/01 23:59:59"
          cmdlist['kicked date'] = "{0:%Y/%m/%d %H:%M:%S}".format(dtnow)
          key = b.new_key ('cmdlist.txt')
          key.set_contents_from_string(json.dumps(cmdlist))
          key.set_acl('public-read')

          if (cmdlist['operation'] == "play"):
             f = openPlaylist()

             if (f[0] == 200):
                print (f[1].splitlines()) # should delete
                rtrncde = playvlc(f[1]).returncode
                if (rtrncde == 0):
                   print ("### successful to kick vlc ###\n")
                else:
                   print ("### fail to kick vlc : code = " + rtrncde + " ###")
             else:
                print ("### something error on reading cmdlist with code=" + str(f[0]) + "\n")
          elif (cmdlist['operation'] == "stop"):
             print ("### stopping vlc ###\n")
             rtncde = stopvlc().returncode
          else:
             print ("operation is not defined yet: " + cmdlist['operation'] + "\n")
          
       else:
          print ("a command, " + cmdlist['operation'] + ", was found, but ")
          print ("this command was requested on " + cmdlist['entry date'])
          print ("then, was done on " + cmdlist['kicked date'] + "\n")
       sleep(15)

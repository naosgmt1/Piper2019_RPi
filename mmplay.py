#!/usr/bin/env python3

import os
import time
import requests
import subprocess

### PERSONAL PARAMETERS
import reference

### DECLARE of PARAMS
f = []

### Fetch to playlist.txt
def openPlaylist():
   global r
   readurl = str("https://" + reference.access_url + "/" + reference.bname + "/" + "playlist.txt")
   print (readurl)              # should delete
   r = requests.get(readurl)
   print (r.status_code)        # should delete
   print (r.text)               # should delete
   print (r)                    # should delete
   if (r.status_code == 200): 
      print ("SUCCESSFUL to GET&READ\n")
   else:
      print ("read error as code =" + r.status_code)
   return [r.status_code, r.text] 

### Play vlc 
def playvlc(plist):
   print ("### start playvlc ###")  # should delete
#   sources = str(" ")
#   sourcelnk = plist.splitlines()
#   print (sourcelnk)             # should delete
#   for sourcelnk in plist.splitlines():
#      sources = sources + sourcelnk + " "
#   print (sources)               # should delete
#   return (subprocess.run (["vlc", str(sources)]))
   cmdlist = ["vlc"]
   cmdlist.extend (plist.splitlines())
   print (cmdlist)
   return (subprocess.call (cmdlist))

### Main Routine ###
if __name__ == "__main__":
   f = openPlaylist()

   print (f)                    # should delete
   print ("\n")                 # should delete
   if (f[0] == 200):
      print ("\n\n")            # should delete
      print (type(f[1]))              # should delete
      print (f[1].splitlines()) # should delete
      rtrncde = playvlc(f[1])
      rtrncde = 0
      if (rtrncde == 0):
         print ("### successful to kick vlc ###")
      else:
         print ("### fail to kick vlc : code = " + rtrncde + " ###")



#!/usr/bin/python3
import smbc
import os, logging

import astm_bidirectional_conf as conf
logging.basicConfig(filename=conf.file2mysql_log_filename,level=logging.DEBUG)  

'''
^B4R|47|^^^^SCAT_WDF|PNG&R&20250221&R&2025_02_24_09_21_1040_WDF.PNG|||N||F||||20250224092138
^C0F
^B5R|48|^^^^SCAT_WDF-CBC|PNG&R&20250221&R&2025_02_24_09_21_1040_WDF_CBC.PNG|||N||F||||20250224092138
^C2D
^B6R|49|^^^^DIST_RBC|PNG&R&20250221&R&2025_02_24_09_21_1040_RBC.PNG|||N||F||||20250224092138
^C08
^B7R|50|^^^^DIST_PLT|PNG&R&20250221&R&2025_02_24_09_21_1040_PLT.PNG|||N||F||||20250224092138
^C33
'''

def get_img_from_machine(workgroupp,usernamee,passwordd,smb_string_with_unix_slash,full_path_with_unix_slash):
  def my_auth_callback_fn(server,share,workgroup,username,password):
    #IPU is workgroup
    return  (workgroupp,usernamee,passwordd)
    #return  ('IPU','sysmax','c9.0')

  ctx = smbc.Context (auth_fn=my_auth_callback_fn)
  logging.debug('smb:{}{}'.format(smb_string_with_unix_slash,full_path_with_unix_slash))
  full_path='smb:{}{}'.format(smb_string_with_unix_slash,full_path_with_unix_slash)
  #This is working. so format like this
  #full_path='smb://IPU/shared'+'/PNG/20250221/2025_02_24_09_21_1040_WDF.PNG'
  logging.debug(full_path)
  f_handle = ctx.open(full_path)
  #return file
  logging.debug("f_handle:{}".format(f_handle))
  data=f_handle.read()
  #o=open("x.png","+bw")
  #o.write(data)
  return data

#example
#data=get_img_from_machine('IPU','sysmax','c9.0','//IPU/shared','/PNG/20250221/2025_02_24_09_21_1040_RBC.PNG')
#o=open("y.png","+bw")
#o.write(data)

'''
>>> # Directory listing example:
>>> import smbc
>>> ctx = smbc.Context (auth_fn=my_auth_callback_fn)
>>> entries = ctx.opendir ("smb://SERVER").getdents ()
>>> for entry in entries:
...     print entry
<smbc.Dirent object "music" (File share) at 0x7fbd7c42b3a0>
<smbc.Dirent object "IPC$" (IPC share) at 0x7fbd7c42b148>
<smbc.Dirent object "Charlie" (Printer share) at 0x7fbd7c42b3c8>
>>> d = ctx.open ("smb://SERVER/music")

>>> # Write file example:
>>> import smbc
>>> import os
>>> ctx = smbc.Context (auth_fn=my_auth_callback_fn)
>>> file = ctx.open ("smb://SERVER/music/file.txt", os.O_CREAT | os.O_WRONLY)
>>> file.write ("hello")

>>> # Read file example:
>>> import smbc
>>> ctx = smbc.Context (auth_fn=my_auth_callback_fn)
>>> file = ctx.open ("smb://SERVER/music/file.txt")
>>> print file.read()
hello


'''

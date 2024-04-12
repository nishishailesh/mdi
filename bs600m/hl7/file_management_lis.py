#!/usr/bin/python3
import datetime,fcntl,os, logging, shutil
class file_management_lis(object):
  def __init__(self,inbox_data,inbox_arch,outbox_data,outbox_arch):
    self.set_inbox(inbox_data,inbox_arch)
    self.set_outbox(outbox_data,outbox_arch)
  def set_inbox(self,inbox_data,inbox_arch):
    self.inbox_data=inbox_data
    self.inbox_arch=inbox_arch
    

  def set_outbox(self,outbox_data,outbox_arch):
    self.outbox_data=outbox_data
    self.outbox_arch=outbox_arch

  def get_first_inbox_file(self):
    self.current_inbox_file=''
    inbox_files=os.listdir(self.inbox_data)
    for each_file in inbox_files:
      if(os.path.isfile(self.inbox_data+each_file)):
        self.current_inbox_file=each_file
        print_to_log('current inbox filepath:',self.inbox_data+self.current_inbox_file)
        try:
          fh=open(self.inbox_data+self.current_inbox_file,'rb')
          fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
          return True
        except Exception as my_ex:
         msg="{} is locked. trying next..".format(self.inbox_data+self.current_inbox_file)
         print_to_log(my_ex,msg)
    return False  #no file to read


  def get_first_outbox_file(self):
    self.current_outbox_file=''
    outbox_files=os.listdir(self.outbox_data)
    for each_file in outbox_files:
      if(os.path.isfile(self.outbox_data+each_file)):
        self.current_outbox_file=each_file
        print_to_log('current outbox filepath:',self.outbox_data+self.current_outbox_file)
        try:
          fh=open(self.outbox_data+self.current_outbox_file,'rb')
          fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
          return True
        except Exception as my_ex:
         msg="{} is locked. trying next..".format(self.outbox_data+self.current_outbox_file)
         print_to_log(my_ex,msg)
    return False  #no file to read

  def get_inbox_filename(self):
    dt=datetime.datetime.now()
    return self.inbox_data+dt.strftime("%Y-%m-%d-%H-%M-%S-%f")

  def get_outbox_filename(self):
    dt=datetime.datetime.now()
    return self.outbox_data+dt.strftime("%Y-%m-%d-%H-%M-%S-%f")


  def archive_outbox_file(self):
    shutil.move(self.outbox_data+self.current_outbox_file, self.outbox_arch+self.current_outbox_file)
    #pass #useful during debugging
    #full path from source to destination prevent exception on ovewriting

  def archive_inbox_file(self):
    shutil.move(self.inbox_data+self.current_inbox_file, self.inbox_arch+self.current_inbox_file)

def print_to_log(object1,object2):
  logging.debug('{} {}'.format(object1,object2))

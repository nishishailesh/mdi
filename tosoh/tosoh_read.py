#!/usr/bin/python3
import sys
import fcntl

####Settings section start#####
input_tty='/dev/ttyS2'
logfile_name='/var/log/tosoh.in.log'
output_folder='/root/tosoh.inbox.data/' #remember ending/
alarm_time=25
log=1	#log=0 to disable logging; log=1 to enable
####Settings section end#####

import logging
logging.basicConfig(filename=logfile_name,level=logging.DEBUG,format='%(asctime)s %(message)s')
if(log==0):
  logging.disable(logging.CRITICAL)
import signal
import datetime
import time
import serial

def signal_handler(signal, frame):
  global x				#global file open
  global byte_array			#global array of byte
  logging.debug('Alarm stopped')
  sgl='signal:'+str(signal)
  logging.debug(sgl)
  logging.debug(frame)
  try:
    if x!=None:
      x.write(''.join(byte_array))
      x.close()
  except Exception as my_ex:
    logging.debug(my_ex)
  logging.debug(byte_array)
  byte_array=[]							#empty array
  logging.debug('Alarm->signal_handler. data may be incomplate')

def get_filename():
  dt=datetime.datetime.now()
  return output_folder+dt.strftime("%Y-%m-%d-%H-%M-%S-%f")

def get_port():
  port = serial.Serial(input_tty,baudrate=9600)
  return port

def my_read(port):
  return port.read(1)

def my_write(port,byte):
  return port.write(byte)

#main loop##########################

signal.signal(signal.SIGALRM, signal_handler)

port=get_port()
byte_array=[]		#initialized to ensure that first byte can be added
status=''
waiting_for_checksum=False
x=None

while True:
  byte=my_read(port)
  logging.debug(byte)
  if(byte==b''):
    logging.debug('<EOF> reached. disconnected?')
  else:
    byte_array=byte_array+[chr(ord(byte))]	#add everything read to array, if not EOF. EOF have no ord

  if(byte==b'\x02' and waiting_for_checksum==False):
    logging.debug('<STX> received , at if loop')
    signal.alarm(0)
    logging.debug('Alarm stopped')
    #byte_array=byte_array+[chr(ord(byte))]	#add everything read to array requred here to add first byte

    if(x==None):
      cur_file=get_filename()					#get name of file to open
      logging.debug('opened file:'+cur_file)
      x=open(cur_file,'w')                                        #open file
      fcntl.flock(x, fcntl.LOCK_EX | fcntl.LOCK_NB)   #lock file

    logging.debug('<STX> received. no <ACK> Sent. This is not classical ASTM. Name of File opened to save data:'+str(cur_file))
    signal.alarm(alarm_time)
    logging.debug('post-stx Alarm started to receive other data')

  elif(byte==b'\x03' and waiting_for_checksum==False):
    logging.debug('<ETX> received, next will be checksum byte (not two character)')
    waiting_for_checksum=True
    logging.debug('<ETX->waiting_for_checksum is set to True')

  elif(waiting_for_checksum==True): #This is OK because of elif
    logging.debug('waiting_for_checksum is True while entering this part of elif')
    waiting_for_checksum=False
    logging.debug('waiting_for_checksum is set to False after entering this part of elif')
    signal.alarm(0)
    logging.debug('Alarm stopped. <BCC> checksum byte received, because this is next to <ETX>')
    num=my_write(port , b'\x06');
    logging.debug('Sending <ACK>. written {} bytes,{}'.format(len(b'\x06'),b'\x06'))
    try:
      x.write(''.join(byte_array))
      byte_array=[]							#empty array
    except Exception as my_ex:
      logging.debug(my_ex)
      logging.debug('Tried to write to a non-existant file??')
    signal.alarm(alarm_time)
    logging.debug('POST <ACK> Alarm started to receive other data')
  elif(byte==b'\x04'):
    logging.debug('<EOT> received.')
    signal.alarm(0)
    logging.debug('Alarm stopped')
    try:
      if x!=None:
        x.write(''.join(byte_array))			#write to file everytime LF received, to prevent big data memory problem
        x.close()
        logging.debug('File closed:')
        x=None
    except Exception as my_ex:
      logging.debug(my_ex)
    byte_array=[]							#empty array      
    logging.debug('byte_array zeroed')

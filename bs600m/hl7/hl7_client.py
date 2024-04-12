#!/usr/bin/python3

import socket,time, signal,logging

TCP_IP = '127.0.0.1'
TCP_PORT = 2575
BUFFER_SIZE = 4096
s=None
def signal_handler(signal, frame):
  print('signal_handler() is called')
   
def read_input():
  data=input('  0. Exit\n\
  1. Send hello message\n\
  2. Send hl7 message\n\
  3. Send first half hl7 message\n\
  4. Send second half hl7 message\n\
  input number:')
  return data
  
def signal_handler(signal, frame):
  logging.debug('Alarm Stopped. Signal:{} Frame:{}'.format(signal,frame))
  logging.debug('Alarm..response NOT received in stipulated time , data receving/sending may be incomplate')

logging.basicConfig(filename='hl7_client.log',level=logging.DEBUG,format='%(asctime)s : %(message)s') 
signal.signal(signal.SIGALRM, signal_handler)
    
while True:
  if s==None:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
      s.connect((TCP_IP, TCP_PORT))
    except Exception as my_ex:
      time.sleep(1)
      continue
    s.setblocking(0)
    
  while True:
    received_data=''
    MESSAGE=b''
    data=read_input()
    if(data=='1'):
      MESSAGE=b'Hellow world'
      s.send(MESSAGE)

    elif(data=='2'):
      MESSAGE=b"\x0bMSH|^~\&|hl7_client.py|debian linux|hl7_general.py|debian linux|198808181126|SECURITY|ORU^R01|MSG00001|P|2.3.1\x0dPID|1||PATID1234^5^M11^ADT1^MR^MCM~123456789^^^USSSA^SS||\x1c\x0d"
      s.send(MESSAGE)

    elif(data=='3'):
      MESSAGE1=b"\x0bMSH|^~\&|ADT1|MCM|Broken1|MCM|198808181126|SECURITY|ADT^A01|MSG"
      MESSAGE2=b"00331|P|2.3.1\x0dPID|1||PATID0000^5^M11^ADT1^MR^MCM~123456789^^^USSSA^SS||\x1c\x0d"
      s.send(MESSAGE1)
      print('Waiting for 2 seconds to send 2nd half of message.................')
      time.sleep(2)
      s.send(MESSAGE2)
    elif(data=='0'):
      s.close()
      quit()
      
    try:
      print('Waiting for 3 seconds before readying to receive message.................')
      time.sleep(3)
      signal.alarm(5)
      print('Waiting for 5 seconds AFTER becoming ready to receive message.................')
      received_data = s.recv(BUFFER_SIZE)
      signal.alarm(0)
      print('Stopping alarm because message is received/ not received for 5 seconds.................')

      print ("((((received data:))))", received_data)
    except Exception as my_ex:
      print ("((((received data:))))", "NOTHING")

#!/usr/bin/python3
import sys,time, logging, socket, select, os, signal, datetime, fcntl, random
import bidirectional_general_conf as conf
from bidirectional_general import bdg
from file_management_lis import file_management_lis
#from mysql_lis import mysql_lis    #Not required for obtaining data and saving as file

def print_to_log(object1,object2):
  logging.debug('{} {}'.format(object1,object2))

class hl7(bdg):
  def __init__(self,host_address,host_port,select_timeout,alarm_time):
    super().__init__(host_address,host_port,select_timeout)
    self.alarm_time=alarm_time
    self.hl7_message_status='EMPTY'
    self.mllp_start_byte=b'\x0b'
    self.mllp_end_byte=b'\x1c'
    self.mllp_newline=b'\x0d'
    self.raw_data=b'';
    #Possible message status
    #START_BYTE_RECEIVED
    #END_BYTE_RECEIVED

    signal.signal(signal.SIGALRM, self.signal_handler)

  def manage_read(self,data):
    self.print_to_log('self.hl7_message_status: on entry',self.hl7_message_status)
    self.print_to_log("hl7::manage_read()  data chunk :",data)

    if(chr(data[0]).encode()==self.mllp_start_byte):
      signal.alarm(0)
      self.print_to_log('Stopping: alarm','')
      self.raw_data=data
      self.hl7_message_status='START_BYTE_RECEIVED'
      self.print_to_log('self.hl7_message_status:',self.hl7_message_status)
      signal.alarm(self.alarm_time) #if en bytes not received in alarm_time, staus will become EMPTY and raw_data will be b''
      self.print_to_log('Starting alarm for seconds:',self.alarm_time)

    else:
      if(self.hl7_message_status=='START_BYTE_RECEIVED'):
        self.raw_data=self.raw_data+data

    if(chr(data[-1]).encode()==self.mllp_newline and chr(data[-2]).encode()==self.mllp_end_byte):
      signal.alarm(0) # alarm not needed
      self.print_to_log('Stopping: alarm','')
      self.print_to_log("end bytes received. hl7::manage_read() full frame :",self.raw_data)
      message_tuple=self.raw_data_to_message_tuple()
      self.respond_to_message(message_tuple)
      self.raw_data=b''
      self.hl7_message_status='EMPTY'
      self.print_to_log('self.hl7_message_status:',self.hl7_message_status)

  def manage_write(self):
    self.print_to_log('bdg::loop->hl7::manage_write():',' This is from hl7 class')
    #Send message in response to write_set->select->writable initiated by manage_read() and initiate_write()
    if(len(self.write_msg)>0):
      self.print_to_log('hl7::manage_write():Following will be sent',self.write_msg)
      try:
        self.conn[0].send(self.write_msg)
        if(self.hl7_message_status=='INITIATE_WRITE'):
          self.hl7_message_status!='EMPTY'
          #'INITIATE_WRITE' is reset
        self.write_msg=b'' #not in astm. because status
      except Exception as my_ex :
        self.print_to_log("Disconnection from client?",my_ex)
    else:
      self.print_to_log('hl7::manage_write()',' No data to write')

  def initiate_write(self):
    self.print_to_log('hl7::initiate_write()',' For managing outbox')
    self.print_to_log('hl7::initiate_write() self.hl7_message_status:',self.hl7_message_status)
    if(self.hl7_message_status!='EMPTY'):
      self.print_to_log('Some activity is going on somewhere else','may be a message is being received. So, doing nothing')
      return
    else:
      self.print_to_log('hl7::initiate_write()  previous hl7_message_status:',self.hl7_message_status)
      self.hl7_message_status!='INITIATE_WRITE'
      self.print_to_log('hl7::initiate_write() changed hl7_message_status:',self.hl7_message_status)
      
    fml=file_management_lis(conf.inbox_data,conf.inbox_arch,conf.outbox_data,conf.outbox_arch)
    if(fml.get_first_outbox_file()==True):                 #There is something to work      
      fd=open(fml.outbox_data+fml.current_outbox_file,'rb')
      fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)   #lock file
      file_data=fd.read() #Whole file without it, no management can be done
      print_to_log('hl7::initiate_write() file_data',file_data)
      signal.alarm(0)
      self.write_set.add(self.conn[0])                      #Add in write set, for next select() to make it writable
      self.error_set=self.read_set.union(self.write_set)    #update error set
      self.write_msg=file_data  #send message
      fd.close()
      fml.archive_outbox_file()
      signal.alarm(self.alarm_time) #if no recv activity on opposite side reset everything
      #however if ack message is received, stop alarm
    else:
      print_to_log('hl7::initiate_write() Nothing in outbox to initiate','going back to loop')


    
  def signal_handler(self,signal, frame):
    self.print_to_log('signal_handler initial status: self.hl7_message_status: ',self.hl7_message_status)
    self.print_to_log('Alarm Stopped','Signal:{} Frame:{}'.format(signal,frame))
    self.print_to_log('Alarm..response NOT received in stipulated time','data receving/sending may be incomplate')
    
    self.raw_data=b''
    self.print_to_log('Initializing raw_data:',self.raw_data)

    self.print_to_log('updating status as EMPTY','data receving/sending may be incomplate')
    self.hl7_message_status='EMPTY'
    self.print_to_log('signal_handler end status: self.hl7_message_status: ',self.hl7_message_status)

  def raw_data_to_message_tuple(self):
    data1=self.raw_data[1:-3]  #remove start, end marker and last new line (which gives one empty member)
    data2=data1.split(b"\r")
    data3=[item.split(b"|") for  item in data2]
    return data3

  def respond_to_message(self,message_tuple):
    if(message_tuple[0][0]==b'MSH'):
      self.print_to_log("MSH is first field of first line:",message_tuple[0][0])
      received_msg_id=message_tuple[0][9]
      self.print_to_log("HL7 MSG received_msg_id:",received_msg_id)
    else:
      self.print_to_log("Doing nothing. Because, MSH is not first field of first line:",message_tuple[0][0])
      return
      
    for message_line in message_tuple:
      self.print_to_log("messageline:",message_line)
      if(message_line[0]==b'MSA'):
        self.print_to_log("This is ACK to message control id:",message_line[2])
        self.raw_data=b''
        self.hl7_message_status='EMPTY'
        self.print_to_log('As ACK self.hl7_message_status:',self.hl7_message_status)
        self.print_to_log("Alarm was started when initiate_write updated write message",' Now as ACK is obtained, so, alarm is closed')
        signal.alarm(0) # this was alarm started during initiate write
        return  #no more action

    dt=datetime.datetime.now()
    msg_time=dt.strftime("%Y%m%d%H%M%S").encode("UTF-8")
    msg_control_id=str(round(1000+random.random()*1000)).encode("UTF-8")
    #msg_control_id=dt.strftime("%Y%m%d%H%M%S%f").encode("UTF-8")

    ack_msg_type={b"QRY^Q02":b"QCK^Q02",b"ORU^R01":b"ACK^R01"}
    #when lis send DSR^Q03 message, analyser respnds by ACK^R03 message

    if(message_tuple[0][8]==b'QRY^Q02'):
      #self.write_msg=b"\x0bMSH|^~\&|||||"+msg_time+b"||"+ack_msg_type[message_tuple[0][8]]+b"|"+msg_control_id+b"|P|2.3.1\x0dMSA|AA|"+received_msg_id+b"|message accepted|||0\x0dQAK|SR|OK\x0d\x1c\x0d"
      #self.write_msg=b"\x0bMSH|^~\&|||||"+msg_time+b"||"+ack_msg_type[message_tuple[0][8]]+b"|"+received_msg_id+b"|P|2.3.1\x0dMSA|AA|"+received_msg_id+b"|message accepted|||0\x0dQAK|SR|OK\x0d\x1c\x0d"
      self.write_msg=b"\x0bMSH|^~\&|||||"+msg_time+b"||"+ack_msg_type[message_tuple[0][8]]+b"|"+received_msg_id+b"|P|2.3.1||||0||UNICODE||\x0dMSA|AA|"+received_msg_id+b"|message accepted|||0|\x0dQAK|SR|OK|\x0d\x1c\x0d"
    if(message_tuple[0][8]==b'ORU^R01'):
      #self.write_msg=b"\x0bMSH|^~\&|||||"+msg_time+b"||"+ack_msg_type[message_tuple[0][8]]+b"|"+msg_control_id+b"|P|2.3.1||||0||UNICODE||\x0dMSA|AA|"+received_msg_id+b"|message accepted|||0\x0d\x1c\x0d"
      #self.write_msg=b"\x0bMSH|^~\&|||||"+msg_time+b"||"+ack_msg_type[message_tuple[0][8]]+b"|"+msg_control_id+b"|P|2.3.1||||0||UNICODE||\x0dMSA|AA|"+received_msg_id+b"|message accepted|||0\x0d\x1c\x0d"
      self.write_msg=b"\x0bMSH|^~\&|||||"+msg_time+b"||"+ack_msg_type[message_tuple[0][8]]+b"|"+received_msg_id+b"|P|2.3.1||||0||UNICODE||\x0dMSA|AA|"+received_msg_id+b"|message accepted|||0\x0d\x1c\x0d"

    fml=file_management_lis(conf.inbox_data,conf.inbox_arch,conf.outbox_data,conf.outbox_arch)
    new_file=fml.get_inbox_filename()
    self.fd=open(new_file,'wb')
    fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)   #lock file
    #Now use this fd for writing
    self.fd.write(self.raw_data)
    print_to_log('File Name:',new_file)
    print_to_log('File Content written:',self.raw_data)
    self.fd.close()
  #not yet used in current script
  def is_received_data_MLLP(self,data):
    #MESSAGE=b"\x0bMSH|^~\&|ADT1|MCM|FINGER|MCM|198808181126|SECURITY|ADT^A01|MSG00001|P|2.3.1\x0dPID|1||PATID1234^5^M11^ADT1^MR^MCM~123456789^^^USSSA^SS||\x1c\x0d"
    start_byte=data[0:1]
    end_bytes=data[len(data)-2:]
    self.print_to_log(b"required start byte is \x0b , data start bye is:",start_byte)
    self.print_to_log(b"required two end bytes are \x1c\x0d , data end two byes are is:",end_bytes)
    if((start_byte,end_bytes)==(b'\x0b',b'\x1c\x0d')):
      self.print_to_log((start_byte,end_bytes) , (start_byte,end_bytes))
      return True
    return False

if __name__=='__main__':
  loglevel=logging.DEBUG
  logging.basicConfig(filename=conf.log_filename,level=loglevel,format='%(asctime)s : %(message)s') 

  print('__name__ is ',__name__,',so running code')
  while True:
    m=hl7(conf.host_address,conf.host_port,conf.select_timeout,alarm_time=conf.alarm_time)
    m.loop()
    #break; #useful during debugging


'''
For MLLP (Minimal Lower Layer Protocol):
 
 dddd
 
  = Start Block character (1 byte)
      ASCII , i.e., <0x0B>. This should not be confused with the ASCII characters
      SOH or STX.
 dddd = Data (variable number of bytes)
      This is the HL7 data content of the block. The data can contain any displayable
      ASCII characters and the carriage return character, .
  = End Block character (1 byte)
      ASCII , i.e., <0x1C>. This should not be confused with the ASCII characters
      ETX or EOT.
  = Carriage Return (1 byte)
      The ASCII carriage return character, i.e., <0x0D>.
'''


'''

b'MSH|^~\\&|||||20240406195330||QRY^Q02|6|P|2.3.1||||||UNICODE|||', b'QRD|20240406195330|R|D|6|||RD|W12123|OTH|||T|', b'QRF||||||RCT|COR|ALL||', b''

2024-04-06 19:26:17,759 : 20 Message line: b'MSH|^~\\&|||||20240406195330||QRY^Q02|6|P|2.3.1||||||UNICODE|||'
2024-04-06 19:26:17,759 : 20 line_list: [b'MSH', b'^~\\&', b'', b'', b'', b'', b'20240406195330', b'', b'QRY^Q02', b'6', b'P', b'2.3.1', b'', b'', b'', b'', b'', b'UNICODE', b'', b'', b'']

2024-04-06 19:26:17,759 : 20 Message line: b'QRD|20240406195330|R|D|6|||RD|W12123|OTH|||T|'
2024-04-06 19:26:17,759 : 20 line_list: [b'QRD', b'20240406195330', b'R', b'D', b'6', b'', b'', b'RD', b'W12123', b'OTH', b'', b'', b'T', b'']

2024-04-06 19:26:17,759 : 20 Message line: b'QRF||||||RCT|COR|ALL||'
2024-04-06 19:26:17,759 : 20 line_list: [b'QRF', b'', b'', b'', b'', b'', b'RCT', b'COR', b'ALL', b'', b'']

https://hl7-definition.caristix.com/v2/HL7v2.5/Fields/MSH.9 is a good source to understand fields of message
message type have three fields

QRY=QRY Query, original mode
Q02=QRY/QCK - Query sent for deferred response

QCK Deferred query
Q02 QRY/QCK - Query sent for deferred response


'''

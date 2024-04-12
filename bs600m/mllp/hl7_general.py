#!/usr/bin/python3
import sys,time, logging, socket, select, os, signal
import bidirectional_general_conf as conf
from bidirectional_general import bdg
from file_management_lis import file_management_lis
#from mysql_lis import mysql_lis    #Not required for obtaining data and saving as file

    
class hl7(bdg):
  
  def __init__(self,host_address,host_port,select_timeout,alarm_time):
    super().__init__(host_address,host_port,select_timeout)
    self.alarm_time=alarm_time
    self.hl7_message=()
    self.hl7_line=b''
    self.hl7_message_status='EMPTY'
    self.mllp_start_byte=b'\x0b'
    self.mllp_end_byte=b'\x1c'
    self.mllp_newline=b'\x0d'
 
    #Possible message status
    #START_BYTE_RECEIVED
    #END_BYTE_RECEIVED
    
    signal.signal(signal.SIGALRM, self.signal_handler)

  def manage_read(self,data):
    self.print_to_log("hl7::manage_read():",data)
    self.analyse_read_data(data)
    '''
    if(self.is_received_data_MLLP(data)):
      self.write_msg=b'Received data is MLLP'
    else:
      self.write_msg=b'Error: >>>>Received data is NOT MLLP'
    '''
    
    self.print_to_log('hl7::manage_read(): sending...',self.write_msg)       

  def manage_write(self):
    self.print_to_log('hl7::manage_write():','I am called by loop()')       
    #Send message in response to write_set->select->writable initiated by manage_read() and initiate_write()
    if(len(self.write_msg)>0):
      self.print_to_log('hl7::manage_write():Following will be sent',self.write_msg) 
      try:
        self.conn[0].send(self.write_msg)
        self.write_msg='' #not in astm. because status 
      except Exception as my_ex :
        self.print_to_log("Disconnection from client?",my_ex)

  def signal_handler(self,signal, frame):
    self.print_to_log('Alarm Stopped','Signal:{} Frame:{}'.format(signal,frame))
    self.print_to_log('Alarm..response NOT received in stipulated time','data receving/sending may be incomplate')


  def analyse_read_data(self,data):
    self.print_to_log("hl7::analyse_read_data():",data)
    for d in data:
      i=chr(d).encode()
      self.print_to_log('self.hl7_message_status:{} '.format(self.hl7_message_status),'data byte:{}'.format(i))
      if(i==self.mllp_start_byte):
        self.hl7_message_status='START_BYTE_RECEIVED'
        self.hl7_message=()
        self.hl7_line=b''
        continue
      if(self.hl7_message_status=='START_BYTE_RECEIVED'):
        if(i==self.mllp_newline):
          self.hl7_message=self.hl7_message+(self.hl7_line,)
          self.hl7_line=b''
          continue
        if(i==self.mllp_end_byte):
          self.hl7_message_status='END_BYTE_RECEIVED'
          self.hl7_message=self.hl7_message+(self.hl7_line,)
          self.hl7_line=b''
          continue
        else:
          self.hl7_line=self.hl7_line+i
        continue          
      if(self.hl7_message_status=='END_BYTE_RECEIVED'):
        if(i==self.mllp_newline):
          self.process_hl7_message(self.hl7_message)
          self.print_to_log("self.message_as_tuple:",self.message_as_tuple,logging.INFO)
         
          self.hl7_message=()
          self.hl7_line=b''
          self.hl7_message_status='EMPTY'
          continue
        else:
          self.print_to_log("END_BYTE_RECEIVED, but,","MLLP NEW LINE not received immediately after. Invalid message??")
          self.print_to_log("So, Initializing hl7_line,","Initializing hl7_message")
          self.hl7_message=()
          self.hl7_line=b''
          self.hl7_message_status='EMPTY'
          continue          

  def process_hl7_message(self,message):
    self.print_to_log("Whole Message--->: ",message,logging.INFO)
    self.message_as_tuple=()
    for i in message:
      self.print_to_log("Message line:",i,logging.INFO)
      line_list=self.process_hl7_line(i)
      self.message_as_tuple=self.message_as_tuple+(line_list,)
    self.analyse_message_tuple()

  def process_hl7_line(self,line):
    line_list=line.split(b"|")
    self.print_to_log("line_list:",line_list,logging.INFO)
    return line_list

  def analyse_message_tuple(self):
    if(self.message_as_tuple[0][0]==b'MSH'):
      self.print_to_log("MSH is first field of first line:",self.message_as_tuple[0][0])
      received_msg_id=self.message_as_tuple[0][9]
      self.print_to_log("HL7 MSG received_msg_id:",received_msg_id)
      self.write_msg=b"\x0bMSH|^~\&|ADT1|MCM|This is ACK message|MCM|198808181126|SECURITY|ADT^A01|"+self.message_as_tuple[0][9]+b"|P|2.3.1\x0dMSA|AA\x1c\x0d"
    else:
      self.print_to_log("MSH is not first field of first line:",self.message_as_tuple[0][0])

    
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
    m=hl7(conf.host_address,conf.host_port,conf.select_timeout,alarm_time=5)
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

#!/usr/bin/python3
import fcntl, signal, logging, sys

import bidirectional_general as astmg
import astm_bidirectional_conf as conf
from astm_bidirectional_common import file_mgmt, print_to_log

#smb specific code
import get_smb
#get_img_from_machine('IPU','sysmax','c9.0','//IPU/shared','/PNG/20250221/2025_02_24_09_21_1040_RBC.PNG')

class astms(astmg.astmg, file_mgmt):
  def __init__(self,inbox_data,inbox_arch,outbox_data,outbox_arch,alarm_time,host_address,host_port,select_timeout):
    self.main_status=0
          #0=neutral
          #1=receiving
          #2=sending

    self.send_status=0
          #1=enq sent
          #2=1st ack received
          #3=data sent
          #4=2nd ack received
          #0=eot sent

    
    self.total_lines=0
    self.byte_data_list=[]
    self.current_line=0
    
    self.set_inbox(inbox_data,inbox_arch)
    self.set_outbox(outbox_data,outbox_arch)

    super().__init__(host_address,host_port,select_timeout)
    
    self.alarm_time=alarm_time
    signal.signal(signal.SIGALRM, self.signal_handler)

  ###################################
  #override this function in subclass
  ###################################
  #read from enq to eot in single file
  #it will have stx->lf segments, with segment number 1...7..0..7
  def manage_read(self,data):
    #EOF is handled in base class
    #for receiving data
    if(data==b'\x05'):
      signal.alarm(0)      
      self.main_status=1
      self.write_msg=b'\x06'
      self.write_set.add(self.conn[0])                      #Add in write set, for next select() to make it writable
      self.error_set=self.read_set.union(self.write_set)    #update error set

      #new file need not be class global (unlike existing file -> which needs to be deleted)
      new_file=self.get_inbox_filename()
      self.fd=open(new_file,'wb')
      fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)   #lock file
      #Now use this fd for stx-etb/etx frame writing
      self.fd.write(data)
      print_to_log('File Content written:',data)
      
      signal.alarm(self.alarm_time)

    elif(data[-1:] == b'\x0a'):
      signal.alarm(0)
      
      if(self.calculate_and_compare_checksum(data)==True):
        print_to_log('checksum matched:','Proceeding to write data')
        self.fd.write(data)
        print_to_log('File Content written:',data)
                     
        self.write_msg=b'\x06'
        self.write_set.add(self.conn[0])                      #Add in write set, for next select() to make it writable
        self.error_set=self.read_set.union(self.write_set)    #update error set      
      else:
        print_to_log('checksum mismatched:','Proceeding to send NAK')
        self.write_msg=b'\x15'
        self.write_set.add(self.conn[0])                      #Add in write set, for next select() to make it writable
        self.error_set=self.read_set.union(self.write_set)    #update error set      
        
      signal.alarm(self.alarm_time)
  
    elif(data==b'\x04'):
      signal.alarm(0)

      self.fd.write(data)
      print_to_log('File Content written:',data)

      self.fd.close()
      self.main_status=0
      self.send_status=0


    elif(data==b'\x06'):            #ACK when sending

      print_to_log("main_status",self.main_status)
      print_to_log("send_status",self.send_status)
      print_to_log("total_lines",self.total_lines)
      print_to_log("current_line",self.current_line)
      print_to_log("byte_data_list",self.byte_data_list)

      if( (self.send_status==1 or self.send_status==2) and (self.current_line<self.total_lines or self.current_line==0 ) ):
        signal.alarm(0)
        self.send_status=2
        print_to_log('send_status=={}'.format(self.send_status),'post-ENQ ACK')

        #writing
        
        self.write_set.add(self.conn[0])                      #Add in write set, for next select() to make it writable
        self.error_set=self.read_set.union(self.write_set)    #update error set
        print_to_log('######current line: ',self.current_line)
       
        if(self.current_line==0):     #open, set data
          self.get_first_outbox_file()                          #set current_outbox file
          fd=open(self.outbox_data+self.current_outbox_file,'rb')
        
          #data must not be >1024
          #it will be ETX data , not ETB data
          #Frame number will always be one and only one
          #line by line data setup
          self.byte_data_list=fd.read(2024).split(b'\x0a')
          print_to_log('byte_data_list',self.byte_data_list)
          
          self.total_lines=len(self.byte_data_list)-1  #python split alway return minimum 1 len list
          self.current_line=0
          print_to_log('total_lines',self.total_lines)
          print_to_log('current line: ',self.current_line)
        
        byte_data=self.byte_data_list[self.current_line]+ b'\x0a'       
        print_to_log('File Content',byte_data)
        chksum=self.get_checksum(byte_data)
        print_to_log('CHKSUM',chksum)
        self.write_msg=byte_data #set message
        self.current_line=self.current_line+1

        #self.send_status=3       
        #data sent -> change status only when really data of stx-lf or anyother-inappropriate frame really sent
        
        #print_to_log('send_status=={}'.format(self.send_status),'changed send_status to 3 (data sent to write buffer)')
        #writing end
        signal.alarm(self.alarm_time) #wait for receipt of second ack
        
      elif(self.send_status==3):
        signal.alarm(0)
        self.send_status=4
        print_to_log('send_status=={}'.format(self.send_status),'post-LF ACK')

        #write
        self.write_set.add(self.conn[0])                      #Add in write set, for next select() to make it writable
        self.error_set=self.read_set.union(self.write_set)    #update error set
        self.write_msg=b'\x04'                                #set message EOT
        print_to_log("main_status",self.main_status)
        print_to_log("send_status",self.send_status)
        print_to_log("total_lines",self.total_lines)
        print_to_log("current_line",self.current_line)
        print_to_log("byte_data_list",self.byte_data_list)
        self.current_line=0
        self.total_lines=0
        print_to_log("main_status",self.main_status)
        print_to_log("send_status",self.send_status)
        print_to_log("total_lines",self.total_lines)
        print_to_log("current_line",self.current_line)
        print_to_log("byte_data_list",self.byte_data_list)
        self.archive_outbox_file()                            
        #self.send_status=0                                    #change only where actually sent
        #self.main_status=0                                   #change only where actually sent
        #print_to_log('send_status=={}'.format(self.send_status),'sent EOT')
        #print_to_log('main_status=={}'.format(self.main_status),'connection is now, neutral')
        #write end
        #alarm not required, no expectation signal.alarm(self.alarm_time) 
        signal.alarm(self.alarm_time) #when EOT is really sent, change status, or if nothing is sent change status using alarm

    elif(data==b'\x15'):            #NAK
      signal.alarm(0)
      self.send_status=4
      print_to_log('send_status=={}'.format(self.send_status),'post-ENQ/LF NAK. Some error')

      #write - same as above
      self.write_set.add(self.conn[0])                      #Add in write set, for next select() to make it writable
      self.error_set=self.read_set.union(self.write_set)    #update error set
      self.write_msg=b'\x04'                                #set message EOT
      self.archive_outbox_file()
      #self.send_status=0                                    #only when actually sent
      #self.main_status=0
      print_to_log('send_status=={}'.format(self.send_status),'initiate_write() sent EOT')
      print_to_log('main_status=={}'.format(self.main_status),'initiate_write() now, neutral')
      #write end        
      #alarm not required, no expectation signal.alarm(self.alarm_time) 
      signal.alarm(self.alarm_time) #when EOT is really sent then change status , or if nothing is sent change status
     
  ###################################
  #override this function in subclass
  ###################################
  #This handles only STX-ETX data. NO STX-ETB management is done
  def initiate_write(self):
    print_to_log('main_status={} send_status={}'.format(self.main_status,self.send_status),'Entering initiate_write()') 
    if(self.main_status==0):
      print_to_log('main_status=={}'.format(self.main_status),'initiate_write() will find some pending work') 
      if(self.get_first_outbox_file()==True):                 #There is something to work      
        signal.alarm(0) 
        self.main_status=2                                    #announce that we are busy sending data
        print_to_log('main_status=={}'.format(self.main_status),'initiate_write() changed main_status to 2 to send data')
        self.write_set.add(self.conn[0])                      #Add in write set, for next select() to make it writable
        self.error_set=self.read_set.union(self.write_set)    #update error set
        self.write_msg=b'\x05'                                #set message ENQ
        #self.send_status=1                                    #status to ENQ sent only when written
        print_to_log('send_status=={}'.format(self.send_status),'initiate_write() sent ENQ to write buffer')
        signal.alarm(self.alarm_time) #wait for receipt of 1st ACK
      else:
        print_to_log('main_status=={}'.format(self.main_status),'no data in outbox. sleeping for a while')
        return
    else:
      print_to_log('main_status={} send_status={}'.format(self.main_status,self.send_status),'busy somewhre.. initiate_write() will not initiate anything') 


  ###################################
  #override this function in subclass
  ###################################
  def manage_write(self):      
    #common code
    #Send message in response to write_set->select->writable initiated by manage_read() and initiate_write()
    print_to_log('Following will be sent',self.write_msg)

    try:
      self.conn[0].send(self.write_msg)
      #self.write_msg='' #not here because write message is evaluated below
    except Exception as my_ex :
      print_to_log("Disconnection from client?",my_ex)                    

    self.write_set.remove(self.conn[0])                   #now no message pending, so remove it from write set
    self.error_set=self.read_set.union(self.write_set)    #update error set

    #specific code for ASTM status update
    #if sending: ENQ, ...LF, EOT is sent
    #ff receiving: ACK, NAK sent (ACK sending donot need to change status, it activates only alarm
    if(self.write_msg==b'\x04'):      #if EOT sent
      self.main_status=0
      self.send_status=0
      print_to_log('main_status={} send_status={}'.format(self.main_status,self.send_status),'.. because EOT is sent') 
      signal.alarm(0)
      print_to_log('Neutral State','.. so stopping alarm') 
    elif(self.write_msg[-1:]==b'\x0a'): #if main message sent
      if(self.current_line>=self.total_lines):
        self.send_status=3
        print_to_log('main_status={} send_status={}'.format(self.main_status,self.send_status),'.. because message is sent(LF)') 
      else:
        pass  #donot change status
        
    elif(self.write_msg==b'\x05'):      #if enq sent
      self.send_status=1
      print_to_log('main_status={} send_status={}'.format(self.main_status,self.send_status),'.. because ENQ is sent') 
    elif(self.write_msg==b'\x06'):      #if ack sent
      print_to_log('main_status={} send_status={}'.format(self.main_status,self.send_status),'.. no change in status ACK is sent') 

    elif(self.write_msg==b'\x15'):      #if NAK sent = EOT sent
      self.main_status=0
      self.send_status=0
      print_to_log('main_status={} send_status={}'.format(self.main_status,self.send_status),'.. because NAK is sent. going neutral') 
      signal.alarm(0)
      print_to_log('Neutral State','.. so stopping alarm') 
    else:                               #if data stream is incomplate/inappropriate containing EOT etc
      self.send_status=3
      print_to_log('main_status={} send_status={}'.format(self.main_status,self.send_status),'.. incomplate message (without LF) sent. EOT will be sent in next round') 

  #######Specific funtions for ASTM        
  def get_checksum(self,data):
    checksum=0
    start_chk_counting=False
    for x in data:
      if(x==2):
        start_chk_counting=True
        #Exclude from chksum calculation
        continue

      if(start_chk_counting==True):
        checksum=(checksum+x)%256

      if(x==3):
        start_chk_counting=False
        #Include in chksum calculation
      if(x==23):
        start_chk_counting=False
        #Include in chksum calculation
 
    two_digit_checksum_string='{:X}'.format(checksum).zfill(2)
    return two_digit_checksum_string.encode()

  def compare_checksum(self, received_checksum, calculated_checksum):
    if(received_checksum==calculated_checksum):
      return True
    else:
      return False

  def calculate_and_compare_checksum(self, data):
    calculated_checksum=self.get_checksum(data)
    received_checksum=data[-4:-2]
    print_to_log(
                      'Calculated checsum={}'.format(calculated_checksum),
                      'Received checsum={}'.format(received_checksum)
                      )
    return self.compare_checksum(received_checksum,calculated_checksum)

  def signal_handler(self,signal, frame):
    print_to_log('Alarm Stopped','Signal:{} Frame:{}'.format(signal,frame))
    print_to_log('change statuses ',' and close file')

    print_to_log('main_status={} send_status={}'.format(self.main_status,self.send_status),' -->previous ') 
    self.send_status=0                                    #data sent
    self.main_status=0    
    print_to_log('current main_status={} send_status={}'.format(self.main_status,self.send_status),' -->current ') 
    
    try:
      if self.fd!=None:        
        self.fd.close()
        print_to_log('self.signal_handler()','file closed')
    except Exception as my_ex:
      print_to_log('self.signal_handler()','error in closing file:{}'.format(my_ex))    
    
    print_to_log('Alarm..response NOT received in stipulated time','data receving/sending may be incomplate')

 
#Main Code###############################
#use this to device your own script
if __name__=='__main__':
  logging.basicConfig(filename=conf.astm_log_filename,level=logging.DEBUG,format='%(asctime)s : %(message)s')   
  
  #print('__name__ is ',__name__,',so running code')
  while True:
    m=astms(conf.inbox_data,conf.inbox_arch,conf.outbox_data,conf.outbox_arch,conf.alarm_time,conf.host_address,conf.host_port,conf.select_timeout)
    m.astmg_loop()
    #break; #useful during debugging  
    

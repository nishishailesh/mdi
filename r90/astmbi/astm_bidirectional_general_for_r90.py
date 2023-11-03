#!/usr/bin/python3
import fcntl, signal, logging, sys

import bidirectional_general as astmg
import astm_bidirectional_conf as conf
from astm_bidirectional_common import file_mgmt, print_to_log

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
  def manage_read(self,data):
    #EOF is handled in base class
    #for receiving data
    if(data[0:1]==b'\x01'):
      print_to_log('first byte of data  is :',data[0])
      signal.alarm(0)
      #new file need not be class global (unlike existing file -> which needs to be deleted)
      new_file=self.get_inbox_filename()
      self.fd=open(new_file,'wb')
      fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)   #lock file
      self.fd.write(data)
      #Now use this fd for writing other data

      #in case of very short data where 1 and 4 are in single chunk of data
      if(data[-1:]==b'\x04'):
        print_to_log('in the same frame last byte of data  is :',data[-1:])
        signal.alarm(0)
        #self.fd.write(data)				#already written
        #print_to_log('File Content written:',data) 	#will log below
        self.fd.close()					#that's all

      print_to_log('File Content written:',data)
      signal.alarm(self.alarm_time)

    elif(data[-1:]==b'\x04'):
      print_to_log('last byte of data  is :',data[-1:])
      signal.alarm(0)
      self.fd.write(data)
      print_to_log('File Content written:',data)
      self.fd.close()

    #unlike astm data, enveloped by stx and etx, Radiometer sends without start and end are received after soh-chunk and before chunk-eot
    else:
      self.fd.write(data)

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
    

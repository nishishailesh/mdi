#!/usr/bin/python3
import sys,time, logging, socket, select, os
import bidirectional_general_conf as conf


  
class bdg(object):
  read_msg=b''
  write_msg=b''

  read_set=set()
  write_set=set()
  error_set=set()

  readable=set()
  writable=set()
  exceptional=set()



  def print_to_log(self,object1,object2,loglevel=logging.DEBUG):
    if(loglevel==logging.INFO):
      logging.info('{} {} {}'.format(logging.INFO,object1,object2))
    elif(loglevel==logging.WARNING):
      logging.warning('{} {}'.format(object1,object2))  
    elif(loglevel==logging.ERROR):
      logging.error('{} {}'.format(object1,object2))
    elif(loglevel==logging.CRITICAL):
      logging.critical('{} {}'.format(object1,object2))    
    else:
      logging.debug('{} {} {}'.format(logging.DEBUG,object1,object2))

  def list_wait(self):
    self.print_to_log('Listening to {} , {} , {} '.
                    format(
                            list(map(socket.socket.fileno,self.read_set)),
                            list(map(socket.socket.fileno,self.write_set)),
                            list(map(socket.socket.fileno,self.error_set))
                            ),
                      'Heard from for {} , {} , {} '.
                    format(
                            list(map(socket.socket.fileno,self.readable)),
                            list(map(socket.socket.fileno,self.writable)),
                            list(map(socket.socket.fileno,self.exceptional))
                            )
                      )
    #'Received for {} , {} , {} '.format(self.readable,self.writable,self.exceptional))
      
  ###################################
  #override this function in subclass, it donot read data, just manages it after getting data from loop
  ###################################
  def manage_read(self,data):
    self.print_to_log("bdg::loop()->bdg::manage_read():",data)
    self.write_msg=b"bdg::manage_read():"+data
  
  ###################################
  #override this function in subclass, it actually sends data
  ###################################
  def manage_write(self):      
    self.print_to_log('bdg::loop->bdg::manage_write():','')       
    if(len(self.write_msg)>0):
      self.print_to_log('bdg::manage_write():Following will be sent',self.write_msg) 
      try:
        self.conn[0].send(self.write_msg)
        self.write_msg=''  
      except Exception as my_ex :
        self.print_to_log("Disconnection from client?",my_ex)                    



  ###################################
  #override this function in subclass if application is not just acting-reacting type
  #once every loop, it will call this function and see if anything needs to be written
  ###################################
  def initiate_write(self):
    self.write_set.add(self.conn[0])                      #Add in write set, for next select() to make it writable
    self.error_set=self.read_set.union(self.write_set)    #update error set
    if(len(self.write_msg)==0):
      self.write_msg=b'Demo initiate_write() override me. send apple, pineapple \n' #set message
    #time.sleep(1) #This is demo function. It will write a lot. So, better to pause a bit # now moved to loop
    
    
             
  def __init__(self,host_address,host_port,select_timeout):
    #logging.basicConfig(filename=conf.log_filename,level=logging.CRITICAL)
    #logging.basicConfig(filename=conf.log_filename,level=logging.DEBUG)
    #self.logger = logging.getLogger('astm_bidirectional_general')
    self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.s.setsockopt(socket.SOL_SOCKET,socket.SO_KEEPALIVE, 1) 
    self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 1)
    self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 3)
    self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)  
    self.select_timeout=select_timeout #second 
    self.host_address=host_address
    self.host_port=host_port
    try:
      self.s.bind((self.host_address,int(self.host_port)))  #it is a tuple
    except Exception as my_exception:      
      self.print_to_log(my_exception,'bind() failed, ip/port correct??Quitting')
      quit()      
    self.s.listen(2)

    self.print_to_log(self.s,'select() is waiting..') 
    self.readable, self.writable, self.exceptional = select.select((self.s,),(self.s,),(self.s,))
    self.print_to_log(self.s,'select() detected activity')
    if(self.s in self.exceptional):
      self.print_to_log(self.s,'some error on socket s. quitting')
      quit() 
    if(self.s in self.writable):
      self.print_to_log(self.s,'Can not understand why s is writting')
      quit() 
    if(self.s in self.readable):
      self.conn = self.s.accept()
      self.print_to_log(self.s,'Connection request is read')

      #Housekeeping read_set etc. after new connection
      self.conn[0].setblocking(0)    
      
      self.read_set={self.s,self.conn[0]}
      self.write_set=set()  #must be managed when send is required, otherwise use 100% CPU to check writable buffer      
      self.write_set.add(self.conn[0])                      #Add in write set, for next select() to make it writable
      
      self.error_set=self.read_set.union(self.write_set)    #update error set
      
  def loop(self):
    #First set
    #not tuple it is unmutable
    #not list, we need uniq values in error list which is sum of read and write
    while True:      
      #self.self.print_to_log('','before select')
      self.readable, self.writable, self.exceptional = select.select(self.read_set,self.write_set,self.error_set,self.select_timeout)
      #self.self.print_to_log('','after select')
      self.list_wait()
      ###if anybody else try to connect, reject it

      if(self.s in self.exceptional):
        self.print_to_log(self.s,'some error on socket s. quitting')
        self.s.shutdown(socket.SHUT_RDWR)
        self.s.close()
        break 

      if(self.s in self.writable):
        self.print_to_log(self.s,'Can not understand why s is writting')
        self.s.shutdown(socket.SHUT_RDWR)
        self.s.close()
        break 

      if(self.s in self.readable):
        dummy_conn = self.s.accept()
        self.print_to_log(self.s,'Connection request is read, This is second connection. We do not want it. shutdown, close')
        dummy_conn[0].shutdown(socket.SHUT_RDWR)
        dummy_conn[0].close()
        
      ###For client do work
      if(self.conn[0] in self.exceptional):
        self.print_to_log(self.conn[0],'some error on socket conn. quitting')
        self.s.shutdown(socket.SHUT_RDWR)
        self.s.close()
        break 

      if(self.conn[0] in self.writable):
        #sending message (somewhere else conn[0] was added in writable and self.write_msg was given value
        self.print_to_log(self.conn[0],'conn is writable. using manage_write()')
        self.manage_write() 
                       
      if(self.conn[0] in self.readable):
        self.print_to_log(self.conn[0],'Conn have sent some data. now using recv() and manage_read()')
        try:
          data=self.conn[0].recv(4096)    ##########READ
          self.print_to_log('bidirectional_general.py::loop() Following is received:',data)  
          self.manage_read(data)
        except Exception as my_exception:      
          self.print_to_log(my_exception,'recv() failed. something sent and then connection closed') 
          self.s.shutdown(socket.SHUT_RDWR)
          self.s.close()
          '''to prevent: DEBUG:root:[Errno 110] Connection timed out recv() failed. something sent and then connection closed
          DEBUG:root:[Errno 98] Address already in use bind() failed, ip/port correct??Quitting'''
          break

        #only EOF is handled here, rest is handled in manage_read()
        #if EOF 1)close socket 2)remove from list 3)accept new
        if(data==b''):
          self.print_to_log(self.conn[0],'Conn have closed, accepting new connection')
          
          #1) close socket
          try:
            self.conn[0].shutdown(socket.SHUT_RDWR)
            self.conn[0].close()
          except Exception as my_ex:
            self.print_to_log('Connection from client closed??',my_ex)  
        
          #2)remove from read list
          
          #no if:() for read_set because, we reached here due to its presence in read_set
          self.read_set.remove(self.conn[0])
          #write list with if exist
          if(self.conn[0] in self.write_set):
            self.write_set.remove(self.conn[0])
          #error list is union
          #so, no need to manage
          #finally error_set
          self.error_set=self.read_set.union(self.write_set)
          
          #3) Accept new, add to read set, this is blocking here. No need to go for initiate_write, because nothing to do
          self.conn = self.s.accept()
          self.print_to_log(self.s,'New Connection request is read')  
          
          #Housekeeping read_set etc. after new connection
          self.conn[0].setblocking(0)    
          
          self.read_set={self.s,self.conn[0]}
          self.write_set=set()  #must be managed when send is required, otherwise use 100% CPU to check writable buffer      
          self.write_set.add(self.conn[0])                      #Add in write set, for next select() to make it writable
          
          self.error_set=self.read_set.union(self.write_set)    #update error set
      
      self.initiate_write()
      time.sleep(1)

#Main Code###############################
#use this to device your own script
if __name__=='__main__':

  logging.basicConfig(filename=conf.log_filename,level=logging.DEBUG,format='%(asctime)s : %(message)s') 

  print('__name__ is ',__name__,',so running code')
  while True:
    m=bdg(conf.host_address,conf.host_port,conf.select_timeout)
    m.loop()
    #break; #useful during debugging

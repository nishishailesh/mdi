#!/usr/bin/python3
STX=b'\x02'
ETX=b'\x03'
EOT=b'\x04'
ETB=b'\x17'
FS=b'\x1c'
GS=b'\x1d'
RS=b'\x1e'
ACK=b'\x06'

import socket,fcntl,os,logging
from lis3_client_common import file_mgmt, print_to_log
import lis3_conf

def get_checksum(data):
  checksum=0
  for x in data:
    checksum=(checksum+x)
  checksum=checksum%256
  two_digit_checksum_string='{:X}'.format(checksum).zfill(2)
  return two_digit_checksum_string.encode()

def analyse_data(data):
  all_list=[]
  texts=data.split(b'\x02')
  for text in texts:
    records=text.split(b'\x1e')
    for record in records:
      fields=record.split(b'\x1c')
      for field in fields:
        group=field.split(b'\x1d')
        all_list.append(group)
  #print(all_list)
  return all_list

def find_data_type(all_list):
  for list in all_list:
    if(list[0]==b'SMP_NEW_DATA'):
      return b'SMP_NEW_DATA'
    if(list[0]==b'SMP_NEW_AV'):
      return b'SMP_NEW_AV'

def find_rSEQ(all_list):
  for list in all_list:
    if(list[0]==b'rSEQ'):
      return list[1]

def find_iPID(all_list):
  for list in all_list:
    if(list[0]==b'iPID'):
      return list[1]


def get_checksum(data):
  checksum=0
  for x in data:
    checksum=(checksum+x)
  checksum=checksum%256
  two_digit_checksum_string='{:X}'.format(checksum).zfill(2)
  return two_digit_checksum_string.encode()



id_req=STX+b'ID_REQ'+FS+RS+ETX+get_checksum(STX+b'ID_REQ'+FS+RS+ETX)+EOT
ack_msg=STX+ACK+ETX+get_checksum(STX+ACK+ETX)+EOT

pre_time_req=STX+b'TIME_REQ'+FS+RS+b'aMOD'+GS+b'0500'+GS+GS+GS+FS+b'iIID'+GS+b'45064'+GS+GS+GS+FS+RS+ETX
time_req=pre_time_req+get_checksum(pre_time_req)+EOT

pre_id_data=STX+b'ID_DATA'+FS+RS+b'aMOD'+GS+b'LIS'+GS+GS+GS+FS+b'iIID'+GS+b'333'+GS+GS+GS+FS+RS+ETX
id_data=pre_id_data+get_checksum(pre_id_data)+EOT

HOST = lis3_conf.host_address  # The server's hostname or IP address
PORT = lis3_conf.host_port        # The port used by the server

#filec=file_mgmt()
#filec.set_inbox(lis3_conf.inbox_data,lis3_conf.inbox_arch)
#filec.set_outbox(lis3_conf.outbox_data,lis3_conf.outbox_arch)

logging.basicConfig(filename=lis3_conf.lis3_log_filename,level=logging.DEBUG,format='%(asctime)s : %(message)s')   

while True:
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    while True:
      data = s.recv(3024)
      #print('RECV:<<<', data)
      all_list=analyse_data(data)
      try:
        s.sendall(ack_msg)
      except Exception as my_ex:
        #print("ERROR:>>>>>",my_ex)
        break
      data_type=find_data_type(all_list)
      if(data_type==b'SMP_NEW_AV'):
        rSEQ=find_rSEQ(all_list)
        #print("rSEQ AVAILABLE==========>",find_rSEQ(all_list))
        pre_smp_req= STX+b'SMP_REQ' +FS+RS+b'aMOD'+GS+b'0500'+GS+GS+GS+FS+b'iIID'+GS+b'45064'+GS+GS+GS+FS+b'rSEQ'+GS+rSEQ+GS+GS+GS+FS+RS+ETX
        smp_req=pre_smp_req+get_checksum(pre_smp_req)+EOT
        try:
          s.sendall(smp_req)
        except Exception as my_ex:
          #print("ERROR:>>>>>",my_ex)
          break
      if(data_type==b'SMP_NEW_DATA'):
        filec=file_mgmt()
        filec.set_inbox(lis3_conf.inbox_data,lis3_conf.inbox_arch)
        filec.set_outbox(lis3_conf.outbox_data,lis3_conf.outbox_arch)

        new_file=filec.get_inbox_filename()
        fd=open(new_file,'wb')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)   #lock file
        #Now use this fd for stx-etb/etx frame writing
        fd.write(data)
        fd.close()

        print_to_log('File Content written:',data)
        #print("rSEQ Received==========>",find_rSEQ(all_list))
        rSEQ=find_iPID(all_list)
        #print("iPID Received ==========>",find_iPID(all_list))

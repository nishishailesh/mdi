#!/usr/bin/python3
STX=b'\x02'
ETX=b'\x03'
EOT=b'\x04'
ETB=b'\x17'
FS=b'\x1c'
GS=b'\x1d'
RS=b'\x1e'
ACK=b'\x06'

import socket,fcntl,os


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
  print(all_list)
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


def get_checksum(data):
  checksum=0
  for x in data:
    checksum=(checksum+x)
  checksum=checksum%256
  two_digit_checksum_string='{:X}'.format(checksum).zfill(2)
  return two_digit_checksum_string.encode()

magic=b''

id_req=STX+b'ID_REQ'+FS+RS+ETX+get_checksum(STX+b'ID_REQ'+FS+RS+ETX)+EOT
ack_msg=STX+ACK+ETX+get_checksum(STX+ACK+ETX)+EOT
#exit()

pre_smp_req= STX+b'SMP_REQ' +FS+RS+b'aMOD'+GS+b'0500'+GS+GS+GS+FS+b'iIID'+GS+b'45064'+GS+GS+GS+FS+b'rSEQ'+GS+b'4'+GS+GS+GS+FS+RS+ETX
smp_req=pre_smp_req+get_checksum(pre_smp_req)+EOT

pre_time_req=STX+b'TIME_REQ'+FS+RS+b'aMOD'+GS+b'0500'+GS+GS+GS+FS+b'iIID'+GS+b'45064'+GS+GS+GS+FS+RS+ETX
time_req=pre_time_req+get_checksum(pre_time_req)+EOT

#pre_ack=STX+ACK+ETX
#ack=pre_ack+get_checksum(pre_ack)+EOT
pre_id_data=STX+b'ID_DATA'+FS+RS+b'aMOD'+GS+b'LIS'+GS+GS+GS+FS+b'iIID'+GS+b'333'+GS+GS+GS+FS+RS+ETX
id_data=pre_id_data+get_checksum(pre_id_data)+EOT

pre_cal_req= STX+b'CAL_REQ' +FS+RS+b'aMOD'+GS+b'0500'+GS+GS+GS+FS+b'iIID'+GS+b'45064'+GS+GS+GS+FS+b'rSEQ'+GS+b'142'+GS+GS+GS+FS+RS+ETX
cal_req=pre_cal_req+get_checksum(pre_cal_req)+EOT

#msgs=(id_req,ack_msg+id_data,ack_msg,time_req,smp_req,cal_req)
str_msgs='0=id_req,1=id_data,2=ack_msg,,3=time_req,4=smp_req,5=cal_req'

HOST = '12.207.3.200'  # The server's hostname or IP address
PORT = 2578        # The port used by the server

while True:
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    #print('SEND:>>>',msgs[int(x)])
    #s.sendall(msgs[int(x)])
    while True:
      data = s.recv(3024)
      print('RECV:<<<', data)
      all_list=analyse_data(data)
      s.sendall(ack_msg)
      data_type=find_data_type(all_list)
      s.sendall(ack_msg)
      if(data_type==b'SMP_NEW_AV'):
        rSEQ=find_rSEQ(all_list)
        #print("rSEQ==========>",find_rSEQ(all_list))
        pre_smp_req= STX+b'SMP_REQ' +FS+RS+b'aMOD'+GS+b'0500'+GS+GS+GS+FS+b'iIID'+GS+b'45064'+GS+GS+GS+FS+b'rSEQ'+GS+rSEQ+GS+GS+GS+FS+RS+ETX
        smp_req=pre_smp_req+get_checksum(pre_smp_req)+EOT
        s.sendall(smp_req)

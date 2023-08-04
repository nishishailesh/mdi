#!/usr/bin/python3
STX=b'\x02'
ETX=b'\x03'
EOT=b'\x04'
ETB=b'\x17'
FS=b'\x1c'
GS=b'\x1d'
RS=b'\x1e'
ACK=b'\x06'

import socket,fcntl,os,logging,time,sys,datetime
from lis3_client_common import file_mgmt, print_to_log, my_sql
import lis3_conf
#For mysql password
sys.path.append('/var/gmcs_config')
import astm_var

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

def find_result(all_list,ex_code):
  for list in all_list:
    if(list[0]==ex_code):
      return list[1]

def get_checksum(data):
  checksum=0
  for x in data:
    checksum=(checksum+x)
  checksum=checksum%256
  two_digit_checksum_string='{:X}'.format(checksum).zfill(2)
  return two_digit_checksum_string.encode()




def get_eid_for_sid_code(self,con,sid,ex_code):
  logging.debug(sid)
  prepared_sql='select examination_id from result where sample_id=%s'
  data_tpl=(sid,)
  logging.debug(prepared_sql)
  logging.debug(data_tpl)

  cur=self.run_query(con,prepared_sql,data_tpl)
  
  eid_tpl=()
  data=self.get_single_row(cur)
  while data:
    logging.debug(data)
    eid_tpl=eid_tpl+(data[0],)
    data=self.get_single_row(cur)
  logging.debug(eid_tpl)
  

  prepared_sqlc='select examination_id from host_code where code=%s and equipment=%s'
  data_tplc=(ex_code,self.equipment)
  logging.debug(prepared_sqlc)
  logging.debug(data_tplc)
  curc=self.run_query(con,prepared_sqlc,data_tplc)
  
  eid_tplc=()
  datac=self.get_single_row(curc)
  while datac:
    logging.debug(datac)
    eid_tplc=eid_tplc+(datac[0],)
    datac=self.get_single_row(curc)
  logging.debug(eid_tplc)

  ex_id=tuple(set(eid_tpl) & set(eid_tplc))
  logging.debug('final examination id:'+str(ex_id))
  if(len(ex_id)!=1):
    msg="Number of examination_id found is {}. only 1 is acceptable.".format(len(ex_id))
    logging.debug(msg)
    return False
  return ex_id[0]

id_req=STX+b'ID_REQ'+FS+RS+ETX+get_checksum(STX+b'ID_REQ'+FS+RS+ETX)+EOT
ack_msg=STX+ACK+ETX+get_checksum(STX+ACK+ETX)+EOT

pre_time_req=STX+b'TIME_REQ'+FS+RS+b'aMOD'+GS+b'0500'+GS+GS+GS+FS+b'iIID'+GS+b'45064'+GS+GS+GS+FS+RS+ETX
time_req=pre_time_req+get_checksum(pre_time_req)+EOT

pre_id_data=STX+b'ID_DATA'+FS+RS+b'aMOD'+GS+b'LIS'+GS+GS+GS+FS+b'iIID'+GS+b'333'+GS+GS+GS+FS+RS+ETX
id_data=pre_id_data+get_checksum(pre_id_data)+EOT

HOST = '12.207.3.200'  # The server's hostname or IP address
PORT = 2578        # The port used by the server

#filec=file_mgmt()
#filec.set_inbox(lis3_conf.inbox_data,lis3_conf.inbox_arch)
#filec.set_outbox(lis3_conf.outbox_data,lis3_conf.outbox_arch)

logging.basicConfig(filename=lis3_conf.lis3_file2mysql_log_filename,level=logging.DEBUG,format='%(asctime)s : %(message)s')   

while True:
  filec=file_mgmt()
  filec.set_inbox(lis3_conf.inbox_data,lis3_conf.inbox_arch)
  filec.set_outbox(lis3_conf.outbox_data,lis3_conf.outbox_arch)
  if(filec.get_first_inbox_file()):
    fh=open(lis3_conf.inbox_data+filec.current_inbox_file,'rb')
    print_to_log('File full path is: ', lis3_conf.inbox_data+filec.current_inbox_file)
    data=fh.read(5000)
    all_list=analyse_data(data)
    print_to_log("all_list>>>>",all_list)

    fh.close()
    #print(all_list)
    filec.archive_inbox_file()
    if(find_data_type(all_list)==b'SMP_NEW_DATA'):
      print_to_log("File type>>>>","SMP_NEW_DATA")
      iPID=find_iPID(all_list)
      print_to_log("Sample_ID>>>>",iPID)
      if(iPID.decode('UTF-8').isnumeric() == False):
        logging.debug('sample_id is not number')
        continue;

      datee=find_result(all_list,b'rDATE')
      print_to_log("Date>>>>",datee)
      good_date=datetime.datetime.strptime(datee.decode('UTF-8'),"%d%b%Y")
      final_date=str(good_date.year)+str(good_date.month).zfill(2)+str(good_date.day).zfill(2)

      timee=find_result(all_list,b'rTIME')
      good_time=datetime.datetime.strptime(timee.decode('UTF-8'),"%H:%M:%S")
      final_time=str(good_time.hour).zfill(2)+str(good_time.minute).zfill(2)+str(good_time.second).zfill(2)
      #aMOD', b'0500', b'', b'', b''], [b'iIID', b'45064', 
      m=my_sql()
      m.equipment='RP500'
      equipment_for_uniq=find_result(all_list,b'aMOD')+find_result(all_list,b'iIID')
      uniq=bytes(final_date+final_time,'UTF-8')+b'|'+equipment_for_uniq

      con=m.get_link(astm_var.my_host,astm_var.my_user,astm_var.my_pass,astm_var.my_db)
      for each_ex in all_list:
        if(len(each_ex)>1):
          print_to_log("ex name>>>>",each_ex[0])
          print_to_log("ex value>>>>",each_ex[1])
          ccc=get_eid_for_sid_code(m,con,iPID,each_ex[0])
          print_to_log("its code is >>>>",ccc)
          prepared_sql='insert into primary_result \
                             (sample_id,examination_id,result,uniq) \
                             values \
                             (%s,%s,%s,%s) \
                             ON DUPLICATE KEY UPDATE result=%s'
          data_tpl=(iPID,ccc,each_ex[1],uniq,each_ex[1])
          if(ccc!=False):
            cur=m.run_query(con,prepared_sql,data_tpl)
  time.sleep(1)


#!/usr/bin/python3
import sys
import fcntl
import logging
import time

from astm_bidirectional_common import my_sql , file_mgmt, print_to_log
#For mysql password
sys.path.append('/var/gmcs_config')

#########Change this if database/password/username changes##########
import astm_var_clg as astm_var
#########Change this if database/password/username changes##########

####Settings section start#####
logfile_name='/var/log/jokoh.out.log'
inbox_data='/root/jokoh.inbox.data/' #remember ending/
inbox_arch='/root/jokoh.inbox.arch/' #remember ending/
log=1	#log=0 to disable logging; log=1 to enable
equipment='JOKOH'

####Settings section end#####

logging.basicConfig(filename=logfile_name,level=logging.DEBUG,format='%(asctime)s %(message)s')
if(log==0):
  logging.disable(logging.CRITICAL)

print_to_log("Logging Test","[OK]")

f=file_mgmt()
f.set_inbox(inbox_data,inbox_arch)
print_to_log("Inbox Data at:",f.inbox_data)
print_to_log("Inbox Archived at:",f.inbox_arch)

def get_eid_for_sid_code(ms,con,sid,ex_code,equipment):
  logging.debug(sid)
  prepared_sql='select examination_id from result where sample_id=%s'
  data_tpl=(sid,)
  logging.debug(prepared_sql)
  logging.debug(data_tpl)

  cur=ms.run_query(con,prepared_sql,data_tpl)

  eid_tpl=()
  data=ms.get_single_row(cur)
  while data:
    logging.debug(data)
    eid_tpl=eid_tpl+(data[0],)
    data=ms.get_single_row(cur)
  logging.debug(eid_tpl)
  

  prepared_sqlc='select examination_id from host_code where code=%s and equipment=%s'
  data_tplc=(ex_code,equipment)
  logging.debug(prepared_sqlc)
  logging.debug(data_tplc)
  curc=ms.run_query(con,prepared_sqlc,data_tplc)
  
  eid_tplc=()
  datac=ms.get_single_row(curc)
  while datac:
    logging.debug(datac)
    eid_tplc=eid_tplc+(datac[0],)
    datac=ms.get_single_row(curc)
  logging.debug(eid_tplc)

  ex_id=tuple(set(eid_tpl) & set(eid_tplc))
  logging.debug('final examination id:'+str(ex_id))
  if(len(ex_id)!=1):
    msg="Number of examination_id found is {}. only 1 is acceptable.".format(len(ex_id))
    logging.debug(msg)
    return False
  return ex_id[0]


def get_eid_for_sid_code_blob(ms,con,sid,ex_code,equipment):
  logging.debug(sid)
  prepared_sql='select examination_id from result_blob where sample_id=%s'
  data_tpl=(sid,)
  logging.debug(prepared_sql)
  logging.debug(data_tpl)

  cur=ms.run_query(con,prepared_sql,data_tpl)
  
  eid_tpl=()
  data=ms.get_single_row(cur)
  while data:
    logging.debug(data)
    eid_tpl=eid_tpl+(data[0],)
    data=ms.get_single_row(cur)
  logging.debug(eid_tpl)
  

  prepared_sqlc='select examination_id from host_code where code=%s and equipment=%s'
  data_tplc=(ex_code,equipment)
  logging.debug(prepared_sqlc)
  logging.debug(data_tplc)
  curc=ms.run_query(con,prepared_sqlc,data_tplc)
  
  eid_tplc=()
  datac=ms.get_single_row(curc)
  while datac:
    logging.debug(datac)
    eid_tplc=eid_tplc+(datac[0],)
    datac=ms.get_single_row(curc)
  logging.debug(eid_tplc)

  ex_id=tuple(set(eid_tpl) & set(eid_tplc))
  logging.debug('final examination id:'+str(ex_id))
  if(len(ex_id)!=1):
    msg="Number of examination_id found is {}. only 1 is acceptable.".format(len(ex_id))
    logging.debug(msg)
    return False
  return ex_id[0]

def analyse_file(fh):
  record=''
  data=fh.read()
  print_to_log("data:",data)

  datetime_of_analysis=data[0:14]
  print_to_log("datetime:",datetime_of_analysis)

  received_sample_id=data[22:39].lstrip().rstrip().decode("UTF-8")
  print_to_log("striped received_sample_id:",received_sample_id)
  if(received_sample_id.isnumeric()==True):
    real_sample_id=received_sample_id
  else:
    real_sample_id=find_sample_id_for_unique_id(received_sample_id)
  if(real_sample_id==False):
    print_to_log("real sample id not found for received sample_id:",received_sample_id)
    print_to_log("Not doing anything:","Good By")
    return False
  else:
    print_to_log("real_sample_id:",real_sample_id)
  item_number1=data[42:44]
  print_to_log("item number1:",item_number1)
  item_value1=data[44:49]
  print_to_log("item value1:",item_value1)
  error_code1=data[50:51]
  print_to_log("error_code1:",error_code1) 

  item_number2=data[51:53]
  print_to_log("item number2:",item_number2)
  item_value2=data[53:58]
  print_to_log("item value2:",item_value2)  
  error_code2=data[59:60]
  print_to_log("error_code2:",error_code2) 

  item_number3=data[60:62]
  print_to_log("item number3:",item_number3)
  item_value3=data[62:67]
  print_to_log("item value3:",item_value3)
  error_code3=data[68:69]
  print_to_log("error_code2:",error_code3) 

  result_dict={item_number1:item_value1,item_number2:item_value2,item_number3:item_value3}
  print_to_log("result_dict:",result_dict)

  prepared_sql='insert into primary_result \
                             (sample_id,examination_id,result,uniq) \
                             values \
                             (%s,%s,%s,%s) \
                             ON DUPLICATE KEY UPDATE result=%s'

  for jeid in result_dict.keys():
    eid=get_eid_for_sid_code(ms,con,sid,ex_code,equipment)
  #data_tpl=(real_sample_id,

def find_sample_id_for_unique_id(uid):
  ms=my_sql()
  con=ms.get_link(astm_var.my_host,astm_var.my_user,astm_var.my_pass,astm_var.my_db)

  logging.debug('find_sample_id_for_unique_id(con,uid): sample id is not number. but,unique id provided is {}'.format(uid))

  prepared_sql='select \
                      examination_id, \
                      json_extract(edit_specification,\'$.unique_prefix\') as unique_prefix, \
                      json_extract(edit_specification,\'$.table\') as id_table \
                  from examination \
                  where \
                      json_extract(edit_specification,\'$.type\')="id_single_sample"';

  logging.debug('find_sample_id_for_unique_id(con,uid): prepared_sql is:\n {}'.format(prepared_sql))
  cur=ms.run_query(con,prepared_sql,())
  logging.debug("one data:{}".format(cur))
  data=ms.get_single_row(cur)
  while data:
    logging.debug("one data:{}".format(data))
    striped_data=(data[0],data[1].lstrip('"').rstrip('"'),data[2].lstrip('"').rstrip('"'))
    logging.debug("one striped data:{}".format(striped_data))
    logging.debug("unique prefix length data in uid is : {} ?=? {} : is unique _prefix is".format(uid[0:len(striped_data[1])],striped_data[1]))
    if(uid[0:len(striped_data[1])]==striped_data[1]):
      #logging.debug(">>>>search table={} , search id is={}".format(striped_data[2], uid[len(striped_data[1]):] ))
      table_name=striped_data[2]
      unique_id=uid[len(striped_data[1]):]
      logging.debug(">>>>search table={} , search id is={}".format(table_name,unique_id))
      prepared_sql_for_finding_sample_id="select sample_id from `"+table_name+"` where id=%s";
      logging.debug("prepared_sql_for_finding_sample_id = {}".format(prepared_sql_for_finding_sample_id))

      data_tpl_for_finding_sample_id=(unique_id,)          # (), (123,) are valid tuple. BUT, (,) (123) are not valid. see type(tpl) at python prompt
      logging.debug("data_tpl_for_finding_sample_id = {}".format(data_tpl_for_finding_sample_id))

      cur_for_finding_sample_id=ms.run_query(con,prepared_sql_for_finding_sample_id,data_tpl_for_finding_sample_id)
      data_for_finding_sample_id=ms.get_single_row(cur_for_finding_sample_id)
      logging.debug('sample id related data found is: {}'.format(data_for_finding_sample_id))
      if(data_for_finding_sample_id != None):
        return data_for_finding_sample_id[0]
      else:
        return False
    data=ms.get_single_row(cur)
  return False



while True:
  if(f.get_first_inbox_file()):
    analyse_file(f.fh)
    f.archive_inbox_file()
  time.sleep(1)

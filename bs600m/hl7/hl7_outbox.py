#!/usr/bin/python3
import sys,time, logging, socket, select, os, signal, datetime, fcntl, MySQLdb,time, datetime, random
import bidirectional_general_conf as conf
from file_management_lis import file_management_lis
from mysql_lis import mysql_lis

#For mysql password
sys.path.append('/var/gmcs_config')
###########Setup this for getting database,user,pass##########
import astm_var_clg as astm_var
##############################################################
mllp_start_byte=b'\x0b'
mllp_end_byte=b'\x1c'
mllp_newline=b'\x0d'

#mysql_db=mysql_lis()
#con=mysql_db.get_link(astm_var.my_host,astm_var.my_user,astm_var.my_pass,astm_var.my_db)

def print_to_log(object1,object2):
  logging.debug('{} {}'.format(object1,object2))

def get_file_raw_data(fml):
  fd=open(fml.inbox_data+fml.current_inbox_file,'rb')
  fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
  file_data=fd.read() #Whole file without it, no management can be done
  print_to_log('is_file_query() file_data',file_data)
  return file_data

def file_to_message_tuple(fml):
  raw_data=get_file_raw_data(fml)
  data1=raw_data[1:-3]  #remove start, end marker and last new line (which gives one empty member)
  data2=data1.split(b"\r")
  data3=[item.split(b"|") for  item in data2]
  print_to_log('data_tuple:',data3)
  return data3


def manage_result(tpl):
  print_to_log("manage_result() data",tpl)
  ex_result_tuple=()
  query_sample_id=b''
  for one_line in tpl:
    if(one_line[0]==b'OBR'):
      query_sample_id=one_line[2].decode("UTF-8")

      #####Unique ID code
      if(query_sample_id.isnumeric() == True):
        real_sample_id=query_sample_id
      else:
        print_to_log('query_sample_id is not number:',query_sample_id)
        ##Now find sample id for it
        real_sample_id=find_sample_id_for_unique_id(con,query_sample_id)
        print_to_log('real_sample_id={}'.format(real_sample_id),'query_sample_id={}'.format(query_sample_id))
        if(real_sample_id!=False):
          real_sample_id=str(real_sample_id)
          print_to_log('real_sample_id after converting to string is: ', real_sample_id)
        else:
          print_to_log('skipping order generation, because, No real_sample_id  is found.for unique ID=', query_sample_id)
          continue;
        print_to_log('final real sample id as str =',real_sample_id)
      #####End of Unique ID code 


  if(real_sample_id!=False):
    for one_line in tpl:
      if(one_line[0]==b'OBX'):
        eid=get_eid_for_sid_code(con,real_sample_id,one_line[3].decode("UTF-8"))
        if(eid is not False):
          uniq='{}|{}'.format(one_line[14].decode("UTF-8"),conf.equipment)
          ex_result_tuple=ex_result_tuple+(  (eid , one_line[5].decode("UTF-8"),uniq), )
        else:
          print_to_log("examination id not found for code=",one_line[3])
          print_to_log("Is examination requested?","Is examination in host_code?")


  print_to_log("query_sample_id (for machine barcode) is ",query_sample_id)
  print_to_log("real_sample_id is ",real_sample_id)
  print_to_log("results are: ",ex_result_tuple)
  prepared_sql='insert into primary_result \
                             (sample_id,examination_id,result,uniq) \
                             values \
                             (%s,%s,%s,%s) \
                             ON DUPLICATE KEY UPDATE result=%s'
  for one_ex in ex_result_tuple:
    data_tpl=(real_sample_id, one_ex[0],one_ex[1] ,one_ex[2],one_ex[1])
    try:
      cur=mysql_db.run_query(con,prepared_sql,data_tpl)
      msg=prepared_sql
      print_to_log('R prepared_sql:',msg)
      msg=data_tpl
      print_to_log('R data tuple:',msg)
      print_to_log('R cursor:',cur)
      mysql_db.close_cursor(cur)
    except Exception as my_ex:
      msg=prepared_sql
      print_to_log('R prepared_sql:',msg)
      msg=data_tpl
      print_to_log('R data tuple:',msg)
      print_to_log('R exception description:',my_ex)


def find_sample_id_for_unique_id(con,uid):
  logging.debug('find_sample_id_for_unique_id(con,uid): sample id is not number. but,unique id provided is {}'.format(uid))

  prepared_sql='select \
                      examination_id, \
                      json_extract(edit_specification,\'$.unique_prefix\') as unique_prefix, \
                      json_extract(edit_specification,\'$.table\') as id_table \
                  from examination \
                  where \
                      json_extract(edit_specification,\'$.type\')="id_single_sample"';

  logging.debug('find_sample_id_for_unique_id(con,uid): prepared_sql is:\n {}'.format(prepared_sql))
  cur=mysql_db.run_query(con,prepared_sql,())
  logging.debug("one data:{}".format(cur))
  data=mysql_db.get_single_row(cur)
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

      cur_for_finding_sample_id=mysql_db.run_query(con,prepared_sql_for_finding_sample_id,data_tpl_for_finding_sample_id)
      data_for_finding_sample_id=mysql_db.get_single_row(cur_for_finding_sample_id)
      logging.debug('sample id related data found is: {}'.format(data_for_finding_sample_id))
      if(data_for_finding_sample_id != None):
        return data_for_finding_sample_id[0]
      else:
        return False
    data=mysql_db.get_single_row(cur)
  return False

def get_eid_for_sid_code(con,sid,ex_code):
  logging.debug(sid)
  prepared_sql='select examination_id from result where sample_id=%s'
  data_tpl=(sid,)
  logging.debug(prepared_sql)
  logging.debug(data_tpl)

  cur=mysql_db.run_query(con,prepared_sql,data_tpl)

  eid_tpl=()
  data=mysql_db.get_single_row(cur)
  while data:
    logging.debug(data)
    eid_tpl=eid_tpl+(data[0],)
    data=mysql_db.get_single_row(cur)
  logging.debug(eid_tpl)


  prepared_sqlc='select examination_id from host_code where code=%s and equipment=%s'
  data_tplc=(ex_code,conf.equipment)
  logging.debug(prepared_sqlc)
  logging.debug(data_tplc)
  curc=mysql_db.run_query(con,prepared_sqlc,data_tplc)

  eid_tplc=()
  datac=mysql_db.get_single_row(curc)
  while datac:
    logging.debug(datac)
    eid_tplc=eid_tplc+(datac[0],)
    datac=mysql_db.get_single_row(curc)
  logging.debug(eid_tplc)

  ex_id=tuple(set(eid_tpl) & set(eid_tplc))
  logging.debug('final examination id:'+str(ex_id))
  if(len(ex_id)!=1):
    msg="Number of examination_id found is {}. only 1 is acceptable.".format(len(ex_id))
    logging.debug(msg)
    return False
  return ex_id[0]

def make_dsr(source_msg_control_id,query_sample_id,ex_tuple):
  dt=datetime.datetime.now()
  msg_time=dt.strftime("%Y%m%d%H%M%S")
  #msg_control_id=dt.strftime("%Y%m%d%H%M%S%f")
  #msg_control_id=dt.strftime("%Y%m%d%H%M%S")
  msg_control_id=str(round(1000+random.random()*1000))
  #MSH='MSH|^~\&|||||'+msg_time+'||DSR^Q03|'+msg_control_id+'|P|2.3.1||||||ASCII|||'
  MSH='MSH|^~\&|||||'+msg_time+'||DSR^Q03|'+source_msg_control_id+'|P|2.3.1||||||ASCII|||'
  MSA='MSA|AA|'+source_msg_control_id+'|Message accepted|||0|'
  ERR='ERR|0|'
  QAK='QAK|SR|OK|'
  QRD='QRD||'+msg_time+'|R|D|2|||RD||OTH|||T|'
  QRF='QRF|||||||RCT|COR|ALL||'
  #DSP01='DSP|1|||||'
  DSP21='DSP|21||'+query_sample_id+'|||'
  DSP22='DSP|22|||||'
  DSP24='DSP|24|||||'
  DSP26='DSP|26||Serum|||'
  DSC='DSC|1|'
  
  message_list=[MSH,MSA,ERR,QAK,QRD,QRF,DSP21,DSP22,DSP24,DSP26]
  count=29
  for ex in ex_tuple:
    message_list=message_list+ [ 'DSP|'+str(count)+'||'+ex+'^^^|||' ]
    count=count+1
  message_list=message_list+ [ DSC ]
  message=mllp_newline.decode("UTF-8").join(message_list)
  message_bytes=message.encode("UTF-8")
  final_message=mllp_start_byte+message_bytes+mllp_newline+mllp_end_byte+mllp_newline
  logging.debug("DSR message:{}".format(final_message))
  return final_message

def manage_query(tpl):
  print_to_log("manage_query() data",tpl)
  source_msg_control_id=tpl[0][9]
  print_to_log("manage_query() source_msg_control_id:",source_msg_control_id)
  query_sample_id=b''
  for one_line in tpl:
    if(one_line[0]==b'QRD'):
      query_sample_id=one_line[8].decode("UTF-8")
      print_to_log("manage_query() query_sample_id:",query_sample_id)

      #####Unique ID code
      if(query_sample_id.isnumeric() == True):
        real_sample_id=query_sample_id
      else:
        print_to_log('query_sample_id is not number:',query_sample_id)
        ##Now find sample id for it
        real_sample_id=find_sample_id_for_unique_id(con,query_sample_id)
        print_to_log('real_sample_id={}'.format(real_sample_id),'query_sample_id={}'.format(query_sample_id))
        if(real_sample_id!=False):
          real_sample_id=str(real_sample_id)
          print_to_log('real_sample_id after converting to string is: ', real_sample_id)
        else:
          print_to_log('skipping order generation, because, No real_sample_id  is found.for unique ID=', query_sample_id)
          continue;
        print_to_log('final real sample id as str =',real_sample_id)
      #####End of Unique ID code

  sql_get_examination='select r.sample_id,r.examination_id, h.code from result r,host_code h \
                       where \
                        r.sample_id=%s and \
                        r.examination_id=h.examination_id and \
                        h.equipment=%s'
  data_tpl=(real_sample_id,conf.equipment)
  logging.debug(sql_get_examination)
  logging.debug(data_tpl)
  cur=mysql_db.run_query(con,sql_get_examination,data_tpl)
  data=mysql_db.get_single_row(cur)
  ex_tuple=()
  while data:
    logging.debug(data)
    ex_tuple=ex_tuple+(data[2],)
    data=mysql_db.get_single_row(cur)
  print_to_log('ex requested for query_sample_id={} and real_sample_id={} are'.format(query_sample_id,real_sample_id),ex_tuple)

  final_str=make_dsr(source_msg_control_id.decode("UTF-8"),query_sample_id,ex_tuple)
  fname=fml.get_outbox_filename()
  print_to_log('file to be written',fname)
  fd=open(fname,'bw')
  fd.write(final_str)
  fd.close()
  print_to_log('file written to outbox .. ',' .. and closed')

if __name__=='__main__':
  logging.basicConfig(filename=conf.outbox_log_filename,level=logging.DEBUG)  

  while True:
    mysql_db=mysql_lis()
    con=mysql_db.get_link(astm_var.my_host,astm_var.my_user,astm_var.my_pass,astm_var.my_db)
    fml=file_management_lis(conf.inbox_data,conf.inbox_arch,conf.outbox_data,conf.outbox_arch)
    if(fml.get_first_inbox_file()):
      tpl=file_to_message_tuple(fml)
      filetype=tpl[0][8]
      print_to_log('Filetype:',filetype)
      if(filetype==b'ORU^R01'):
        manage_result(tpl)
      elif(filetype==b'QRY^Q02'):
        manage_query(tpl)
      fml.archive_inbox_file() #comment, useful during debugging
    time.sleep(1)
    #break; #useful during debugging

#!/usr/bin/python3
import os
import sys
#apt install python3-mysqldb
import MySQLdb
import time
import logging
import fcntl
import datetime

import astm_bidirectional_conf as conf
from astm_file2mysql_bidirectional_general import astm_file

#smb specific code
import get_smb
#get_img_from_machine('IPU','sysmax','c9.0','//IPU/shared','/PNG/20250221/2025_02_24_09_21_1040_RBC.PNG')

#For mysql password
sys.path.append('/var/gmcs_config')

###########Setup this for getting database,user,pass##########
import astm_var_clg as astm_var
##############################################################


#classes#################################
class astm_file_xl1000(astm_file):
  equipment=conf.equipment  #no self. only inside defination 

  def get_sample_type_vitros_code(self,sample_id):
    con=self.get_link(astm_var.my_host,astm_var.my_user,astm_var.my_pass,astm_var.my_db)
    sample_requirement_id=1000   
    prepared_sql='select vitros_sample_type from lis_to_vitros_sample_type,result where \
                    sample_id=%s and examination_id=%s and result=lis_sample_type'
                    
    data_tpl=(sample_id,sample_requirement_id)
    
    try:          
      cur=self.run_query(con,prepared_sql,data_tpl)
      row=self.get_single_row(cur)
      print_to_log('sample type for vitros:',row)
      self.close_cursor(cur)
      return row[0]
    except Exception as my_ex:
      print_to_log('exception description:',my_ex)
      return '0'
      
  def manage_final_data(self):
    print_to_log('manage_final_data():final_data',self.final_data)
    con=self.get_link(astm_var.my_host,astm_var.my_user,astm_var.my_pass,astm_var.my_db)
       
    prepared_sql='insert into primary_result \
                             (sample_id,examination_id,result,uniq) \
                             values \
                             (%s,%s,%s,%s) \
                             ON DUPLICATE KEY UPDATE result=%s'

    '''
    sample_id	bigint(20)	
    examination_id	int(11)	
    uniq	varchar(100)	
    result	mediumblob NULL	
    fname	varchar(100) NULL	
    extra	varchar(5000) NULL	
    '''
    prepared_sql_blob='insert into primary_result_blob \
                             (sample_id,examination_id,result,uniq,fname) \
                             values \
                             (%s,%s,%s,%s,%s) \
                             ON DUPLICATE KEY UPDATE result=%s , fname=%s'

    prepared_sql_q='select r.sample_id,r.examination_id, h.code from result r,host_code h \
                      where \
                        r.sample_id=%s and \
                        r.examination_id=h.examination_id and \
                        h.equipment=%s'
                      
    for each_sample in self.final_data:
      print_to_log('full data of each_sample:',each_sample)
      print_to_log('For sample_id: full data of each_sample[0]:',each_sample[0])
      print_to_log('Associated details of sample: full data of each_sample[1]:',each_sample[1])

      #######sample id unique id code########
      print_to_log('sample_id related field each_sample[0] value:',each_sample[0])
      print_to_log("taking relevent data:",each_sample[0].split(self.s3))
      print_to_log("taking relevent data:",each_sample[0].split(self.s3)[2])
      print_to_log("taking relevent data:",each_sample[0].split(self.s3)[2].strip(' '))
      query_sample_id=each_sample[0].split(self.s3)[2].strip(' ')
      print_to_log('query_sample_id:',query_sample_id)

      #####Unique ID code
      if(query_sample_id.isnumeric() == True):
        real_sample_id=query_sample_id
      else:
        print_to_log('query_sample_id is not number:',query_sample_id)
        ##Now find sample id for it
        real_sample_id=self.find_sample_id_for_unique_id(con,query_sample_id)
        print_to_log('real_sample_id={}'.format(real_sample_id),'query_sample_id={}'.format(query_sample_id))
        if(real_sample_id!=False):
          real_sample_id=str(real_sample_id)
          print_to_log('real_sample_id after converting to string is: ', real_sample_id)
        else:
          print_to_log('skipping order generation, because, No real_sample_id  is found for unique ID=', query_sample_id)
          continue;
        print_to_log('final real sample id as str =',real_sample_id)
      ####### end of sample id unique id code########
      print_to_log('real_sample_id:',real_sample_id)

      #Now analyse supplied data
      for each_record in each_sample[1]:
        if(each_record[0]=='R'):


          ''' 
          ^B4R|47|^^^^SCAT_WDF|PNG&R&20250221&R&2025_02_24_09_21_1040_WDF.PNG|||N||F||||20250224092138
          ^B5R|48|^^^^SCAT_WDF-CBC|PNG&R&20250221&R&2025_02_24_09_21_1040_WDF_CBC.PNG|||N||F||||20250224092138
          ^B6R|49|^^^^DIST_RBC|PNG&R&20250221&R&2025_02_24_09_21_1040_RBC.PNG|||N||F||||20250224092138
          ^B7R|50|^^^^DIST_PLT|PNG&R&20250221&R&2025_02_24_09_21_1040_PLT.PNG|||N||F||||20250224092138
          '''
          #########Starting analysis############
          print_to_log('R tuple:',each_record)
          ex_code=each_record[2].split(self.s3)[4]
          ex_result=each_record[3]
          print_to_log('machine supplied ex_id is: ',ex_code)
          print_to_log('machine supplied ex_result is: ',ex_result)
          print_to_log('can unique string made from each_record[12] + conf.equipment: ',each_record[12] +"|"+conf.equipment)
          uniq='{}|{}'.format(each_record[12],conf.equipment)

          img_type_machine_ex_names=('SCAT_WDF','SCAT_WDF-CBC','DIST_RBC','DIST_PLT')
          if(ex_code in  img_type_machine_ex_names):
            examination_id=self.get_eid_for_sid_code_blob(con,real_sample_id,ex_code)
          else:
            examination_id=self.get_eid_for_sid_code(con,real_sample_id,ex_code)

          print_to_log('LIS software examination_id for machine supplied ex_code is: ',examination_id)
          if(examination_id==False):
            msg="Skipping the while loop once"
            print_to_log(msg,' .. because no eid for this sid and this code')
            continue
          print_to_log('Final Pair is examination_id={}'.format(examination_id),'ex_result={}'.format(ex_result))

          if(ex_code not in  img_type_machine_ex_names):
            try:
              data_tpl=(real_sample_id,examination_id,ex_result,uniq,ex_result)
              print_to_log("data_tpl=",data_tpl)
              msg=prepared_sql
              print_to_log('R prepared_sql:',msg)
              msg=data_tpl
              print_to_log('R data tuple:',msg)
              cur=self.run_query(con,prepared_sql,data_tpl)
              print_to_log('R cursor:',cur)
              self.close_cursor(cur)
            except Exception as my_ex:
              msg=prepared_sql
              print_to_log('R prepared_sql:',msg)
              msg=data_tpl
              print_to_log('R data tuple:',msg)
              print_to_log('R exception description:',my_ex)
          else:
            try:
              print_to_log('ex_code is {}. So blob management...:', ex_code)
              print_to_log('R tuple:',each_record)
              #DEBUG:root:R tuple: ('R', '47', '^^^^SCAT_WDF', 'PNG&R&20250221&R&2025_02_24_09_21_1040_WDF.PNG', '', '', 'N', '', 'F', '', '', '', '20250224092138')
              print_to_log('File path field is:',each_record[3])
              print_to_log('File path could be:',each_record[3].replace("&R&",'/'))
              print_to_log('final File path with slash will be:','/'+each_record[3].replace("&R&",'/'))
              file_path='/'+each_record[3].replace("&R&",'/')
              img_file_name=file_path.split('/')[3]	#actually 2 but due to added slash one more
              img_data=get_smb.get_img_from_machine(conf.smb_workgroup,
                                                    conf.smb_username,
                                                    conf.smb_password,
                                                    conf.smb_string_with_unix_slash,
                                                    file_path)
              #f=open("x.png","+bw")
              #f.write(img_data)
              #prepared_sql_blob='insert into primary_result_blob \
              #                              (sample_id,examination_id,result,uniq,fname) \
              #                              values \
              #                              (%s,%s,%s,%s,%s,%s,%s) \
              #                              ON DUPLICATE KEY UPDATE result=%s , fname=%s'

              data_tpl=(real_sample_id,examination_id,img_data,uniq,img_file_name,img_data,img_file_name)
              print_to_log("R data_tpl=",data_tpl)
              print_to_log('R prepared_sql_blob:',prepared_sql_blob)
              cur=self.run_query(con,prepared_sql_blob,data_tpl)
              print_to_log('R cursor:',cur)
              self.close_cursor(cur)
            except Exception as my_ex:
              print_to_log('exception:ex_code is {}. So blob management...:',ex_code)
              msg=prepared_sql_blob
              print_to_log('R prepared_sql_blob:',msg)
              msg=data_tpl
              print_to_log('R data tuple:',msg)
              print_to_log('R exception description:',my_ex)



        if(each_record[0]=='Q'):

          #set sample_id, there is ^ for profile and ` for multiple sample_id in xl1000
          #Q|1|^1007149`1007152`1007151`1007150`1007148|||S|||||||O
          #in R record it is plain
          #sample_id=each_sample[0].split(self.s3)[1]
          sample_id_list=each_sample[0].split(self.s3)[1].split(self.s2)
          print_to_log('sample_id_list:',sample_id_list)

          for query_sample_id in sample_id_list:
            query_sample_id=query_sample_id.rstrip(' ')
            #####Unique ID code
            if(query_sample_id.isnumeric() == True):
              real_sample_id=query_sample_id
            else:
              print_to_log('query_sample_id is not number:',query_sample_id)
              ##Now find sample id for it
              real_sample_id=self.find_sample_id_for_unique_id(con,query_sample_id)
              print_to_log('real_sample_id={}'.format(real_sample_id),'query_sample_id={}'.format(query_sample_id))
              if(real_sample_id!=False):
                real_sample_id=str(real_sample_id)
                print_to_log('real_sample_id after converting to string is: ', real_sample_id)
              else:
                print_to_log('skipping order generation, because, No real_sample_id  is found.for unique ID=', query_sample_id)
                continue;
              print_to_log('final real sample id as str =',real_sample_id)


            #get examination codes
            print_to_log('Q tuple:',each_record)
            print_to_log('Q prepared_sql:',prepared_sql_q)
            data_tpl=(real_sample_id,self.equipment)
            print_to_log('Q data tuple:',data_tpl)
            try:
              cur=self.run_query(con,prepared_sql_q,data_tpl)
              print_to_log('Q cursor:',cur)
            except Exception as my_ex:
              print_to_log('Q exception description:',my_ex)
            
            single_q_data=self.get_single_row(cur)
            requested_examination_code=()
            while(single_q_data):
              print_to_log('examination_id={}'.format(single_q_data[1]), ' code={}'.format(single_q_data[2]))
              requested_examination_code=requested_examination_code+(single_q_data[2],)
              single_q_data=self.get_single_row(cur)
            
            self.close_cursor(cur)
            
            print_to_log(
                        'real_sample_id {}: query_sample_id {}:'.format(real_sample_id,query_sample_id),
                        'Following is requested {}:'.format(requested_examination_code)
                        )
                        
            #order_to_send=self.make_order(sample_id,requested_examination_code)
            #This changes were made to accoumodate unique id
            order_to_send=self.make_order(query_sample_id,real_sample_id,requested_examination_code)
            print_to_log('Order ready',order_to_send)
            fname=self.get_outbox_filename()
            print_to_log('file to be written',fname)
            fd=open(fname,'bw')
            fd.write(order_to_send)
            fd.close()
            print_to_log('file written to outbox .. ',' .. and closed')
          
    self.close_link(con)

  def make_order(self,query_sample_id,real_sample_id,requested_examination_code):
    #for Vitros
    #^^^1.0000+002+1.0 ^^^manualDil+testcode+autodilu~testcode+autodilu~testcode+autodilu
    three_caret=self.s3*3
    three_caret_byte=three_caret.encode()
    join_str='+1.0'+self.s2
    ex_code_str=three_caret_byte+b'1.0000+'+join_str.join(requested_examination_code).encode()+b'+1.0'+self.s2.encode()
    ex_code_str=ex_code_str[:-1]

    dt=datetime.datetime.now()
    time_now=dt.strftime("%Y%m%d%H%M%S")

    #frame_number=1 in headerline, but not used, because only one frame(STX-ETX-LF will be sent per EOT)
    #5 = serum for vitros

    print_to_log('seperators ',self.s1+self.s2+self.s3+self.s4)

    #Old
    '''
    header_line=  b'1H'+self.s1.encode()+self.s2.encode()+self.s3.encode()+self.s4.encode()+b'|||3600796||||||||LIS2-A|'+time_now.encode()
    patient_line= b'2P|1|NOPID|||NONAME^^|||F'
    order_line=   b'3O|1|'+sample_id.encode()+b'||'+ex_code_str+b'|R||'+time_now.encode()+b'||||N||||5||||||||||O'
    terminator_line=b'4L|1|N'
    str_for_checksum=b'\x02'+header_line+b'\x0d'+patient_line+b'\x0d'+order_line+ b'\x0d'+terminator_line+ b'\x0d\x03'
    checksum=self.get_checksum(str_for_checksum)
    print_to_log('Calculated checksum=: ',checksum)
    final_message=str_for_checksum+checksum+b'\x0d\x0a'
    print_to_log('Final message: ',final_message)
    return final_message
    '''

    vitros_sample_code=self.get_sample_type_vitros_code(real_sample_id).encode()
    header_line=  b'1H'+self.s1.encode()+self.s2.encode()+self.s3.encode()+self.s4.encode()+b'|||3600796||||||||LIS2-A|'+time_now.encode()
    patient_line= b'2P|1|NOPID|||NONAME^^|||F'
    #order_line=   b'3O|1|'+sample_id.encode()+b'||'+ex_code_str+b'|R||'+time_now.encode()+b'||||N||||5||||||||||O'
    order_line=   b'3O|1|'+query_sample_id.encode()+b'||'+ex_code_str+b'|R||'+time_now.encode()+b'||||N||||'+vitros_sample_code+b'||||||||||O'
    terminator_line=b'4L|1|N'
    return self.format_astm_message(header_line)+self.format_astm_message(patient_line)+self.format_astm_message(order_line)+self.format_astm_message(terminator_line)

  def format_astm_message(self,message):
    message_for_checksum=b'\x02'+message+b'\x0d\x03'
    message_checksum=self.get_checksum(message_for_checksum)
    print_to_log('Calculated checksum=: ',message_checksum)
    final_message=message_for_checksum+message_checksum+b'\x0d\x0a'
    print_to_log('Final message: ',final_message)
    return final_message
 
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

  def get_eid_for_sid_code_blob(self,con,sid,ex_code):
    logging.debug(sid)
    prepared_sql='select examination_id from result_blob where sample_id=%s'
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

  def find_sample_id_for_unique_id(self,con,uid):
    logging.debug('find_sample_id_for_unique_id(self,con,uid): sample id is not number. but,unique id provided is {}'.format(uid))
    
    prepared_sql='select \
                        examination_id, \
                        json_extract(edit_specification,\'$.unique_prefix\') as unique_prefix, \
                        json_extract(edit_specification,\'$.table\') as id_table \
                    from examination \
                    where \
                        json_extract(edit_specification,\'$.type\')="id_single_sample"';
    
    logging.debug('find_sample_id_for_unique_id(self,con,uid): prepared_sql is:\n {}'.format(prepared_sql))
    cur=self.run_query(con,prepared_sql,())
    logging.debug("one data:{}".format(cur))
    data=self.get_single_row(cur)
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
        
        cur_for_finding_sample_id=self.run_query(con,prepared_sql_for_finding_sample_id,data_tpl_for_finding_sample_id)
        data_for_finding_sample_id=self.get_single_row(cur_for_finding_sample_id)
        logging.debug('sample id related data found is: {}'.format(data_for_finding_sample_id))
        if(data_for_finding_sample_id != None):
          return data_for_finding_sample_id[0]
        else:
          return False
      data=self.get_single_row(cur)
    return False






def print_to_log(object1,object2):
  logging.debug('{} {}'.format(object1,object2))
  
#Main Code###############################
#use this to device your own script


if __name__=='__main__':
  logging.basicConfig(filename=conf.file2mysql_log_filename,level=logging.DEBUG)  

  #print('__name__ is ',__name__,',so running code')
  while True:
    m=astm_file_xl1000()
    if(m.get_first_inbox_file()):
      m.analyse_file()
      m.mk_tuple()
      m.manage_final_data() #specific for each equipment/lis
      m.archive_inbox_file() #comment, useful during debugging
    time.sleep(1)
    #break; #useful during debugging


#!/usr/bin/python3
import sys
import fcntl
import logging
import time
import matplotlib.pyplot as plt 
import io

from astm_bidirectional_common import my_sql , file_mgmt, print_to_log
#For mysql password
sys.path.append('/var/gmcs_config')
import astm_var
####Settings section start#####
logfile_name='/var/log/tosoh.out.log'
inbox_data='/root/tosoh.inbox.data/' #remember ending/
inbox_arch='/root/tosoh.inbox.arch/' #remember ending/
log=1	#log=0 to disable logging; log=1 to enable
equipment='VITROS3600'


tosoh_to_lis={
      "SA1C":5174,
      "chromatogram":5178
  }
  

tosoh_to_lis_qc={
      "SA1C":9222,
      "chromatogram":9223
  }
    
####Settings section end#####

logging.basicConfig(filename=logfile_name,level=logging.DEBUG,format='%(asctime)s %(message)s')
if(log==0):
  logging.disable(logging.CRITICAL)
  
print_to_log("Logging Test","[OK]")

f=file_mgmt()
f.set_inbox(inbox_data,inbox_arch)
print_to_log("Inbox Data at:",f.inbox_data)
print_to_log("Inbox Archived at:",f.inbox_arch)

def analyse_file(fh):
  record_dict={}
  record=''
  sub_dict_5={}
  sub_dict_7={}
  all_record=() #empty tuple
  while True:
      data=fh.read(1)
      #print_to_log("byte:",data)
      if data==b'':
        break
      elif data==b'\x02':
        #print_to_log("<STX>:","It starts here")
        record=''
      elif data==b'\x03':
        #print_to_log("<ETX>:","It ends here")
        #print_to_log("record:",record)
        #print_to_log("record:",{record[0:1]:record[1:]})
        #print_to_log("record number:",record[0:1])
        #print_to_log("record dict:",record_dict)
        if(record[0:1]=='5'):
          sub_dict_5.update({record[1:3]:record[3:]})
          record_dict.update({ record[0:1] : sub_dict_5 })
        elif(record[0:1]=='7'):
          sub_dict_7.update({record[1:4]:record[4:]})
          record_dict.update({ record[0:1] : sub_dict_7 })
        elif(record[0:1]=='8'):
          record_dict.update({record[0:1]:record[1:]})
          #This is last record. prepare for next
          all_record=all_record+(record_dict,) #add to tuple
          #now reset everything for possible next record in a multirecord file
          record_dict={}
          record=''
          sub_dict_5={}
          sub_dict_7={}
          
        else:
          record_dict.update({record[0:1]:record[1:]})        
        #print_to_log("record dict:",record_dict)
      else:
        record=record+chr(ord(data))
  return all_record
  
def manage_all_record(all_record_tuple):
  for record in all_record_tuple:
    manage_record(record)


def mk_histogram_from_tuple(xy,heading,x_axis,y_axis,axis_range_tuple):
  #print(x)
  #print(y)
  plt.plot(xy[0], xy[1]) 
  plt.xlabel(x_axis) 
  plt.ylabel(y_axis)
  plt.axis(axis_range_tuple) 
  plt.title(heading) 
  f = io.BytesIO()
  plt.savefig(f, format='png')
  f.seek(0)
  data=f.read()
  f.close()
  plt.close()	#otherwise graphs will be overwritten, in next loop
  return data

def manage_record(record):
  #print_to_log("single record:",record)
  print_to_log("########",'#########')
  print_to_log("### managing record 1 (Sample Information):",record['1'])
  print_to_log("0 =STD mode, 1 = VAR mode, 2 = β-thalassemia mode :",record['1'][0:1].strip())
  print_to_log("0 = STAT, 1 = transport (LA), 2 = loader : ",record['1'][1:2].strip())
  sample_id=record['1'][2:].strip()
  print_to_log("sample_id:",sample_id)
  print_to_log("### managing record 2 (Sample Number) Not used at all here : ",record['2'])
  uniq=equipment+'_'+record['2']
  print_to_log("### managing record 3 (Measurement value):",record['3'])
  print_to_log("Flag ??:",record['3'][0:2])
  
  hba1=record['3'][2:2+5].strip()
  print_to_log("HbA1 (Total Glycated Hemoglobin:)",hba1)
  
  hba1a=record['3'][7:7+5].strip()
  print_to_log("HbA1a: ",hba1a)
  
  hba1b=record['3'][12:12+5].strip()
  print_to_log("HbA1b: ",hba1b)
  
  hbf=record['3'][17:17+5].strip()
  print_to_log("HbF: ",hbf)

  hba1cl=record['3'][22:22+5].strip()
  print_to_log("HbA1c (Labile): ",hba1cl)

  hba1cs=record['3'][27:27+5].strip()
  print_to_log("HbA1c (Stable): ",hba1cs)

  hba0=record['3'][32:32+5].strip()
  print_to_log("HbA0: ",hba0)
  
  hv0=record['3'][37:37+5].strip()
  print_to_log("Hb V0 (HbD): ",hv0)
  
  hv1=record['3'][42:42+5].strip()
  print_to_log("Hb V1 (HbS): ",hv1)
  
  hv2=record['3'][47:47+5].strip()
  print_to_log("Hb V1 (HbC): ",hv2)
  
  phv3=record['3'][52:52+5].strip()
  print_to_log("Possible Hb V2 (HbE) ???: ",phv3)  

  auc=record['3'][57:57+5].strip()
  print_to_log("Total area under curve ???: ",auc)

  print_to_log("### managing record 4 (Data collection information):",record['4'])
  print_to_log("Chromatogram Start time: ",record['4'][0:4].strip())
  print_to_log("Reading taken every X100 milliseconds : ",record['4'][4:5].strip())
  print_to_log("Number of peaks : ",record['4'][5:7].strip())
  print_to_log("Number of raw data sets : ",record['4'][7:11].strip())

  print_to_log("### managing record 5 (Peak data) Not used currently: ",record['5'])
  #'5 1A1A  B  15 650  15  77  81    4.35  0.5'
  #'112123451123412341234123412341234567812345'
  #'   01234567890123456789012345678901234567890
  #dictionary.items() converts it in to list of tuples
  #example
  #>>> x
  #{1: 2, 3: 4, 'a': 'b'}
  #>>> x.items()
  #dict_items([(1, 2), (3, 4), ('a', 'b')])

  peak_data_dict={}
  for peak_number,peak_data in record['5'].items():
    print_to_log("pick number:{}, ".format(peak_number),"peak_data:{}".format(peak_data))
    print_to_log("pick number:{}, ".format(peak_number),
"peak_name:{}, \
peak_type:{}, \
base_start:{}, \
base_end:{}, \
peak_start:{}, \
peak_top:{}, \
peak_end:{}, \
peak_area:{}, \
peak_%:{}, "
                  .
                  format(
                          peak_data[0:5].strip(),
                          peak_data[5:6].strip(),
                          peak_data[6:6+4].strip(),
                          peak_data[10:10+4].strip(),
                          peak_data[14:14+4].strip(),
                          peak_data[18:18+4].strip(),
                          peak_data[22:22+4].strip(),
                          peak_data[26:26+8].strip(),
                          peak_data[34:34+5].strip(),
                        )
                )

    peak_data_dict.update({peak_data[0:5].strip():{"peak_persent":peak_data[34:34+5].strip()}})
  print_to_log("peak_data_dict:",peak_data_dict)                    
  print_to_log("### managing record 6: (nothing inside. Just end of record 5)",record['6'])
  print_to_log("### managing record 7: (data points)",record['7'])
  
  x_values=()
  y_values=()
  x_counter=0
  step=(0.2/60)
  
  for point_set,points in record['7'].items():
    print_to_log("point_set: {}".format(point_set),"points: {}".format(points))
    x_values=x_values+(x_counter,x_counter+step*1,x_counter+step*2,x_counter+step*3,x_counter+step*4,
                    x_counter+step*5,x_counter+step*6,x_counter+step*7,x_counter+step*8,x_counter+step*9)
    x_counter=x_counter+step*10
    y_values=y_values+(float(points[0:9].strip()),float(points[9:18].strip()),float(points[18:27].strip()),float(points[27:36].strip()),float(points[36:45].strip()),
                        float(points[45:54].strip()),float(points[54:63].strip()),float(points[63:72].strip()),float(points[72:81].strip()),float(points[81:90].strip()))
  print_to_log("x_values",x_values)
  print_to_log("y_values",y_values)
  axis_range_tuple=(min(x_values),max(x_values),min(y_values),max(y_values)/20)
  png=mk_histogram_from_tuple((x_values,y_values),'HbA1c HPLC Chromatogram','(Retention time) mintues','Absorbance',axis_range_tuple)
  #fff=open('/root/d.png','wb')
  #fff.write(png)
  #fff.close() 

  print_to_log("### managing record 8: (Calibration Information) Not used",record['8'])

  #Now update mysql database
  ms=my_sql()
  con=ms.get_link(astm_var.my_host,astm_var.my_user,astm_var.my_pass,astm_var.my_db)
  prepared_sql='insert into primary_result \
                             (sample_id,examination_id,result,uniq) \
                             values \
                             (%s,%s,%s,%s) \
                             ON DUPLICATE KEY UPDATE result=%s'

  prepared_sql_blob='insert into primary_result_blob \
                             (sample_id,examination_id,result,uniq) \
                             values \
                             (%s,%s,%s,%s) \
                             ON DUPLICATE KEY UPDATE result=%s'
                             
  data_tpl=(sample_id,tosoh_to_lis['SA1C'],peak_data_dict['SA1C']['peak_persent'],uniq,peak_data_dict['SA1C']['peak_persent'])
  
  if(sample_id.rstrip(' ').isnumeric() == False):
    print_to_log('sample id is not nuumberic?:',sample_id)
    return False;
    
  try:          
    cur=ms.run_query(con,prepared_sql,data_tpl)
    msg=prepared_sql
    print_to_log('prepared_sql:',msg)
    msg=data_tpl
    print_to_log('data tuple:',msg)
    print_to_log('cursor:',cur)            
    ms.close_cursor(cur)
  
  except Exception as my_ex:
    msg=prepared_sql
    print_to_log('prepared_sql:',msg)
    msg=data_tpl
    print_to_log('data tuple:',msg)
    print_to_log('exception description:',my_ex)
  
  data_tpl=(sample_id,tosoh_to_lis['chromatogram'],png,uniq,png)

  try:          
    cur=ms.run_query(con,prepared_sql_blob,data_tpl)
    msg=prepared_sql_blob
    print_to_log('prepared_sql:',msg)
    #msg=data_tpl
    #print_to_log('data tuple:',msg)
    #print_to_log('cursor:',cur)            
    ms.close_cursor(cur)
  
  except Exception as my_ex:
    msg=prepared_sql_blob
    print_to_log('prepared_sql:',msg)
    #msg=data_tpl
    #print_to_log('data tuple:',msg)
    print_to_log('exception description:',my_ex)

while True:
  if(f.get_first_inbox_file()):
    all_record_tuple=analyse_file(f.fh)
    #print_to_log("all record:",all_record_tuple)
    manage_all_record(all_record_tuple)
    f.archive_inbox_file()
    time.sleep(1)

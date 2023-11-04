#!/usr/bin/python3
astm_log_filename='/var/log/r90_read.log'
file2mysql_log_filename='/var/log/r90_write.log'
#if you wish to be specific
#host_address='12.207.3.240'
#host_address='11.207.1.1'
#if you wish general declaration
host_address=''
host_port='3000'
select_timeout=1
alarm_time=10
#trailing slash is must to reconstruct path
inbox_data='/root/r90.inbox.data/'
inbox_arch='/root/r90.inbox.arch/'
outbox_data='/root/r90.outbox.data/'
outbox_arch='/root/r90.outbox.arch/'

#following is used to search hostcode and create uniq string for primary results
equipment='R9-402016'
#following is used for to create uniq string for primary results
serial='402016'
#following is used to find equipment
equipment_examination_id=9000
equipment_serial_number_examination_id=9001
equipment_specimen_number_examination_id=9002

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
equipment='R9'
serial='402016'

#!/usr/bin/python3
astm_log_filename='/var/log/bs600m_astm_read.log'
file2mysql_log_filename='/var/log/bs600m_astm_write.log'
#if you wish to be specific
#host_address='12.207.3.240'
#host_address='11.207.1.1'
#if you wish general declaration
host_address=''
host_port='7118'
select_timeout=1
alarm_time=10
#trailing slash is must to reconstruct path
inbox_data='/root/bs600m.inbox.data/'
inbox_arch='/root/bs600m.inbox.arch/'
outbox_data='/root/bs600m.outbox.data/'
outbox_arch='/root/bs600m.outbox.arch/'
equipment='BS600M'

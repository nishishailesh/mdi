#!/usr/bin/python3
astm_log_filename='/var/log/NXL_1000_read.log'
file2mysql_log_filename='/var/log/NXL_1000_write.log'
host_address=''
host_port='5000'
select_timeout=1
alarm_time=10
#trailing slash is must to reconstruct path
inbox_data='/root/NXL_1000.inbox.data/'
inbox_arch='/root/NXL_1000.inbox.arch/'
outbox_data='/root/NXL_1000.outbox.data/'
outbox_arch='/root/NXL_1000.outbox.arch/'
equipment='NXL_1000'

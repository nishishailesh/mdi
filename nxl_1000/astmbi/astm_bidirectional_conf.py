#!/usr/bin/python3
astm_log_filename='/var/log/nxl_1000_read.log'
file2mysql_log_filename='/var/log/nxl_1000_write.log'
#host_address='12.207.3.240'
#host_address='11.207.1.1'
host_address=''
host_port='2578'
select_timeout=1
alarm_time=10
#trailing slash is must to reconstruct path
inbox_data='/root/nxl1000.inbox.data/'
inbox_arch='/root/nxl1000.inbox.arch/'
outbox_data='/root/nxl1000.outbox.data/'
outbox_arch='/root/nxl1000.outbox.arch/'
equipment='NXL_1000'

#!/usr/bin/python3
astm_log_filename='/var/log/cobas411_read.log'
file2mysql_log_filename='/var/log/cobas411_write.log'
#host_address='12.207.3.240'
#host_address='11.207.1.1'
host_address=''
host_port='7119'
select_timeout=1
alarm_time=10
#trailing slash is must to reconstruct path
inbox_data='/root/cobas411.inbox.data/'
inbox_arch='/root/cobas411.inbox.arch/'
outbox_data='/root/cobas411.outbox.data/'
outbox_arch='/root/cobas411.outbox.arch/'
equipment='COBAS411'

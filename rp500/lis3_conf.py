#!/usr/bin/python3
lis3_log_filename='/var/log/rp500_read.log'
lis3_file2mysql_log_filename='/var/log/rp500_write.log'
#if you wish to be specific
#host_address='12.207.3.240'
#host_address='11.207.1.1'
#if you wish general declaration
host_address='172.16.2.200'
host_port=2578
select_timeout=1
alarm_time=10
#trailing slash is must to reconstruct path
inbox_data='/root/rp500.inbox.data/'
inbox_arch='/root/rp500.inbox.arch/'
outbox_data='/root/rp500.outbox.data/'
outbox_arch='/root/rp500.outbox.arch/'
equipment='RP500'
model_string=b'0500'
# if there is # in front, that line will be ignored
serial_string=b'53726'






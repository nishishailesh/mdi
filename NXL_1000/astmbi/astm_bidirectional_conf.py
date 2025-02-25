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

#following is useful for fatching hemogram images/histograms from windows file server
#import get_smb
#get_img_from_machine('IPU','sysmax','c9.0','//IPU/shared','/PNG/20250221/2025_02_24_09_21_1040_RBC.PNG')
smb_workgroup='IPU'
smb_username='sysmax'
smb_password='c9.0'
smb_string_with_unix_slash='//IPU/shared'
#smb_full_path_with_unix_slash provided by machine

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

#For mysql password
sys.path.append('/var/gmcs_config')
import astm_var

def get_sample_type_vitros_code(sample_id):
  m=astm_file()
  con=m.get_link(astm_var.my_host,astm_var.my_user,astm_var.my_pass,astm_var.my_db)
  sample_requirement_id=1000   
  prepared_sql='select vitros_sample_type from lis_to_vitros_sample_type,result where \
                  sample_id=%s and examination_id=%s and result=lis_sample_type'
                  
  data_tpl=(sample_id,sample_requirement_id)
  
  try:          
    cur=m.run_query(con,prepared_sql,data_tpl)
    row=m.get_single_row(cur)
    print(row)
    m.close_cursor(cur)
    return row[0]
  except Exception as my_ex:
    print('exception description:',my_ex)
    return None

get_sample_type_vitros_code('1001000')
get_sample_type_vitros_code('1184973')

'''
-- Adminer 4.7.1 MySQL dump

SET NAMES utf8;
SET time_zone = '+00:00';
SET foreign_key_checks = 0;
SET sql_mode = 'NO_AUTO_VALUE_ON_ZERO';

SET NAMES utf8mb4;

DROP TABLE IF EXISTS `lis_to_vitros_sample_type`;
CREATE TABLE `lis_to_vitros_sample_type` (
  `lis_sample_type` varchar(100) NOT NULL,
  `vitros_sample_type` varchar(10) NOT NULL,
  PRIMARY KEY (`lis_sample_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `lis_to_vitros_sample_type` (`lis_sample_type`, `vitros_sample_type`) VALUES
('Plain-Blood-BI',	'5'),
('Plain-Swab-BI',	'10');

-- 2021-06-15 19:00:29
'''

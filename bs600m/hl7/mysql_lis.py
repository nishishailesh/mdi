#!/usr/bin/python3
import MySQLdb,logging

class mysql_lis(object):
  def get_link(self,my_host,my_user,my_pass,my_db):
    con=MySQLdb.connect(my_host,my_user,my_pass,my_db)
    logging.debug(con)
    if(con==None):
      if(debug==1): logging.debug("Can't connect to database")
    else:
      pass
      logging.debug('connected')
      return con

  def run_query(self,con,prepared_sql,data_tpl):
    cur=con.cursor()
    cur.execute(prepared_sql,data_tpl)
    con.commit()
    msg="rows affected: {}".format(cur.rowcount)
    logging.debug(msg)
    return cur

  def get_single_row(self,cur):
    return cur.fetchone()

  def close_cursor(self,cur):
    cur.close()

  def close_link(self,con):
    con.close()

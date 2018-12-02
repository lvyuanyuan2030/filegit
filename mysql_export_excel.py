#!/usr/bin/env python
# coding: utf-8

#将MySQL表格内容导出到excel文件

#这三行代码是防止在python2上面编码错误的，在python3上面不要要这样设置
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import MySQLdb
import xlwt

def sql_export_excel(): 
	try:
		#连接MySQL
		conn = MySQLdb.connect(host='localhost',user='root',passwd='deepctrl',db='IPs',charset='utf8')
		cursor = conn.cursor()

		#选择表格所有内容
		sql = "select * from validIPURL"
		count = cursor.execute(sql) 
		print '--------------------------'
		print 'has %s record' % count 

		#重置游标位置  
		cursor.scroll(0,mode='absolute')  

		#获取所有表格内容  
		results = cursor.fetchall()  

		#获取MYSQL里的数据字段  
		fields = cursor.description 

		#首先，将字段写入到EXCEL新表的第一行  
		wbk = xlwt.Workbook()  
		sheet = wbk.add_sheet('sheet1',cell_overwrite_ok=True)  
		for ifs in range(0,len(fields)):  
			sheet.write(0,ifs,fields[ifs][0])  
			
		#然后，将表格内容写入到EXCEL后续行
		ics=1  
		jcs=0  
		for ics in range(1,len(results)+1):  
			for jcs in range(0,len(fields)):  
				sheet.write(ics,jcs,results[ics-1][jcs])  
		wbk.save('/home/deepctrl/Desktop/validIP.xlsx')  

	except MySQLdb.Error,e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1]) 

# main
if __name__ == '__main__':

	sql_export_excel()

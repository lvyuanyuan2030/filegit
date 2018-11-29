# -*- coding: utf-8 -*-
#这三行代码是防止在python2上面编码错误的，在python3上面不要要这样设置
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import MySQLdb
import csv
import jieba
import jieba.analyse
from ipcrawler.items import *

firsttime = True

class IpcrawlerPipeline(object):
	def process_item(self, item, spider):

		global firsttime

		if isinstance(item, IpcrawlerItem):
			ID = item['ID']
			url = item['url']
			title = item['title']
			ICP = item['ICP']
			text = item['main_text']
			maxnum_nexturls = item['maxnum_nexturls']

			#if maxnum_nexturls == 0:
			key = jieba.analyse.textrank(text, topK=10)
			keywords = '/'.join(key)
		
			try:
				#连接MySQL
				con = MySQLdb.connect(host='localhost',user='root',passwd='123456',db='IPs',charset='utf8')
				cur = con.cursor()
				con.set_character_set('utf8')

				#创建表，注意设置编码为utf8，否则中文出错
				if firsttime:
					firsttime = False 
					cur.execute("drop table if exists validIP")
					cur.execute("create table validIP(%s) default charset = utf8" %('ID VARCHAR(500),url VARCHAR(500),title VARCHAR(500),ICP VARCHAR(500),keywords VARCHAR(500)'))
				#插入表
				try:
					sql = "INSERT INTO validIP VALUES ('%s','%s','%s','%s','%s')"%(ID,url,title,ICP,keywords)
					cur.execute(sql) 
					#提交
					con.commit() 
				#异常回滚，打印错误信息
				except MySQLdb.Error,e:
					print "Mysql Error %d: %s" % (e.args[0], e.args[1]) 
					con.rollback()
				#关闭游标和连接
				cur.close() 
				con.close() 
			except MySQLdb.Error,e:
				print "Mysql Error %d: %s" % (e.args[0], e.args[1]) 


			if text:
				txttitle= str(ID) +'.txt'
				with open(txttitle, 'w') as f:
					f.write(text)

		if isinstance(item, IpNextcrawlerItem):
			last_ID = item['last_ID']
			next_ID = item['next_ID']
			next_text = item['next_text']
			num_url = item['num_url']
			maxnum_urls = item['maxnum_urls']
			all_text = item['all_text']

			#if num_url == maxnum_urls:
			key = jieba.analyse.textrank(all_text, topK=10)
			keywords = '/'.join(key)

			try:
				#连接MySQL
				con = MySQLdb.connect(host='localhost',user='root',passwd='123456',db='IPs',charset='utf8')
				cur = con.cursor()
				con.set_character_set('utf8')

				#update表
				try:
					sql = "UPDATE validIP SET keywords = '%s' WHERE ID ='%d' "%(keywords,last_ID)
					cur.execute(sql) 
					#提交
					con.commit() 
				#异常回滚，打印错误信息
				except MySQLdb.Error,e:
					print "Mysql Error %d: %s" % (e.args[0], e.args[1]) 
					con.rollback()
				#关闭游标和连接
				cur.close() 
				con.close() 
			except MySQLdb.Error,e:
				print "Mysql Error %d: %s" % (e.args[0], e.args[1]) 

			if next_text:
				next_txttitle= next_ID +'.txt'
				with open(next_txttitle, 'w') as f:
					f.write(next_text)

		return item


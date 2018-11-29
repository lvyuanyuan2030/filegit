# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import scrapy
import time
import xlrd
import csv
import socket
import re
#from scrapy_redis.spiders import RedisSpider
from scrapy import Request
from ipcrawler.items import *
from bs4 import BeautifulSoup

class IPSpider(scrapy.Spider):	#没有使用RedisSpider类
	name = 'ipcrawler'

	num_url = 0
	nexturlnum_dict = {}
	text_dict ={}
	comm_ports_list = [80,8080,443]	#常用端口列表
	base = [str(x) for x in range(10)] + [ chr(x) for x in range(ord('A'),ord('A')+6)]

	def start_requests(self):
		realiplist = []
		realiplist = self.readIPlist()

		self.nexturlnum_dict = self.nexturlnum_dict.fromkeys(list(range(1,len(realiplist))),0)
		self.text_dict = self.text_dict.fromkeys(list(range(1,len(realiplist))),'')

		for ip in realiplist: 
			for port in self.comm_ports_list:
				if port != 443:
					url = 'http://'+ str(ip)+':'+ str(port)
				else:
					url = "https://"+ str(ip)
				yield Request(url, callback=self.parse, meta={'ip':ip,'port':port})

	def parse(self, response):
		item = IpcrawlerItem()
		if response.status == 200:
			#ID
			self.num_url += 1
			ID = self.num_url
			item['ID'] = ID

			#url,buyong response.url
			ip = response.meta['ip']
			port = response.meta['port']
			if port != 443:
				url = 'http://'+ str(ip)+':'+ str(port)
			else:
				url = "https://"+ str(ip)
			item['url'] = url

			#title
			soup = BeautifulSoup(response.text, "html.parser")
			titles = soup.select('title')
			if len(titles) > 0:
				title = titles[0].text
			else:
				title = ""
			item['title'] = title

			#main_text
			main_text = soup.get_text("|", strip=True)	#beautifulsoup解析后为unicode编码格式字符串
			main_text.replace('\r','|')
			self.text_dict[ID] = main_text
			item['main_text'] = main_text

			#ICP
			if main_text:
				compile_rule = re.compile(u'([\u4e00-\u9fa5]ICP.*?号[-\d*]*)', re.I)
				compile_list = re.findall(compile_rule, main_text)
				ICP = ''.join(compile_list).decode('utf-8')	#将Unicode转码utf-8
			item['ICP'] = ICP

			#next_urls
			next_urls = []
			t1 = soup.select('a')
			if len(t1) > 0:
				for t2 in t1:
					if t2.get('href'):
						next_urls.append(t2.get('href'))
			item['next_urls'] = next_urls

			#maxnum_nexturls
			maxnum_nexturls = len(next_urls)
			item['maxnum_nexturls'] = maxnum_nexturls

			yield item

			if maxnum_nexturls > 0:
				for url in next_urls:
					yield Request(url, callback=self.parse_nextpage,meta={'ID':ID,'maxnum_nexturls':maxnum_nexturls})


	def parse_nextpage(self, response):
		item = IpNextcrawlerItem()
		if response.status == 200:
			#next_text
			soup = BeautifulSoup(response.text, "html.parser")
			strilist_next = soup.get_text("|", strip=True)	#beautifulsoup解析后为unicode编码格式字符串
			strilist_next.replace('\r','|')
			item['next_text'] = strilist_next

			ID = response.meta['ID']
			self.nexturlnum_dict[ID] +=1
			if self.nexturlnum_dict[ID] <= response.meta['maxnum_nexturls']:
				self.text_dict[ID] += strilist_next

			item['last_ID'] = ID
			item['next_ID'] = str(ID) + '-'+ str(self.nexturlnum_dict[ID])
			item['num_url'] = self.nexturlnum_dict[ID]
			item['maxnum_urls'] = response.meta['maxnum_nexturls']
			item['all_text'] = self.text_dict[ID]

		yield item


	#读取excel文件，获取ip段地址，生成所有ip列表
	def readIPlist(self):
		iplist = []
		alliplist = []

		#self.write_csvhead()

		data=xlrd.open_workbook('/home/lyy/ipconn/IP.xlsx')
		sheet = data.sheets()[0]
		
		for i in range(sheet.nrows):
			startip = sheet.cell(i,0).value.encode('utf-8')
			endip = sheet.cell(i,1).value.encode('utf-8')
			iplist.append([startip,endip])

		#生成所有ip列表
		for i in iplist:
			startip = i[0]
			endip = i[1]
			alliplist += self.iplistgena(startip,endip)

		return alliplist

	#给定ip段，生成所有ip列表
	def iplistgena(self,string_startip,string_endip):
		realiplist = []
		#分割IP，然后将其转化为8位的二进制代码
		start = string_startip.split('.')
		start_a = self.dec2bin80(start[0])
		start_b = self.dec2bin80(start[1])
		start_c = self.dec2bin80(start[2])
		start_d = self.dec2bin80(start[3])
		start_bin = start_a + start_b + start_c + start_d
		#将二进制代码转化为十进制
		start_dec = self.bin2dec(start_bin)

		end = string_endip.split('.')
		end_a = self.dec2bin80(end[0])
		end_b = self.dec2bin80(end[1])
		end_c = self.dec2bin80(end[2])
		end_d = self.dec2bin80(end[3])
		end_bin = end_a + end_b + end_c + end_d
		#将二进制代码转化为十进制
		end_dec = self.bin2dec(end_bin)

		#十进制相减，获取两个IP之间有多少个IP
		count = int(end_dec) - int(start_dec)

		#生成IP列表
		for i in range(0,count + 1):
			#将十进制IP加一，再转化为二进制（32位补齐）
			plusone_dec = int(start_dec) + i
			plusone_dec = str(plusone_dec)
			address_bin = self.dec2bin320(plusone_dec)
			#分割IP，转化为十进制
			address_a = self.bin2dec(address_bin[0:8])
			address_b = self.bin2dec(address_bin[8:16])
			address_c = self.bin2dec(address_bin[16:24])
			address_d = self.bin2dec(address_bin[24:32])
			address = address_a + '.'+ address_b +'.'+ address_c +'.'+ address_d
			realiplist.append(address)
	
		return realiplist

	#十进制0~255转化为二进制,补0到8位
	def dec2bin80(self, string_num):
		num = int(string_num)
		mid = []
		while True:
			if num == 0: break
			num,rem = divmod(num, 2)
			mid.append(self.base[rem])

		result = ''.join([str(x) for x in mid[::-1]])
		length = len(result)
		if length < 8:
			result = '0' * (8 - length) + result
		return result

	#十进制0~255转化为二进制,补0到32位
	def dec2bin320(self, string_num):
		num = int(string_num)
		mid = []
		while True:
			if num == 0: break
			num,rem = divmod(num, 2)
			mid.append(self.base[rem])

		result = ''.join([str(x) for x in mid[::-1]])
		length = len(result)
		if length < 32:
			result = '0' * (32 - length) + result
		return result

	#二进制转换为十进制
	def bin2dec(self, string_num):
		return str(int(string_num, 2))
		
	#创建csv文件，写入首行表头内容
	def write_csvhead(self):
		with open("validurl2.csv","w") as csvfile:
			writer = csv.writer(csvfile)
			writer.writerow(['ValidURL','webtitle','webtext'])

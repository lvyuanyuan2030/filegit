#!/usr/bin/env python
# coding: utf-8

#通过搜狗搜索中的微信搜索入口来爬取公共号文章，用pandas存储所有文章信息为cvs格式文件+存储所有文章正文内容为txt文本
#用pandas方式存储csv文件，是字典方式，而字典是无序的，所以列的顺序不是按照字典顺序放的，是随机的

#get_selenium_js_html：获取公共号首页内容，用的是webdriver.PhantomJS，前提是selenium为老版本2，换其他浏览器再试试

#这三行代码是防止在python2上面编码错误的，在python3上面不要要这样设置
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
 
from urllib import quote
from pyquery import PyQuery as pq
from selenium import webdriver
from bs4 import BeautifulSoup

import requests
import time
import re
import os
import pandas as pd

class weixin_spider:

	def __init__(self, keywords):
		' 构造函数 '
		self.keywords = keywords
		# 搜狐微信搜索链接入口
		self.sogou_search_url = 'http://weixin.sogou.com/weixin?type=1&query=%s&ie=utf8&s_from=input&_sug_=n&_sug_type_=' % quote(self.keywords)
		
		# 爬虫伪装头部设置
		self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0'}
		
		# 设置操作超时时长
		self.timeout = 5
		
		# 爬虫模拟在一个request.session中完成
		self.s = requests.Session()

		

	#搜索入口地址，以公众号为关键字搜索该公众号	
	def get_search_result_by_keywords(self):
		self.log('搜索地址为：%s' % self.sogou_search_url)
		return self.s.get(self.sogou_search_url, headers=self.headers, timeout=self.timeout).content
	
	#获得公众号主页地址
	def get_wx_url_by_sougou_search_html(self, sougou_search_html):
		#以下两种方式都可以
		#通过pyquery的方式处理网页内容，类似用beautifulsoup，但是pyquery和jQuery的方法类似，找到公众号主页地址
		#doc = pq(sougou_search_html)
		#return doc('div[class=txt-box]')('p[class=tit]')('a').attr('href')

		#通过beautifsoup，找到公众号主页地址
		soup = BeautifulSoup(sougou_search_html,'html.parser')
		return soup.find(class_ = 'tit').a['href']

	#使用webdriver加载公众号主页内容，主要是js渲染的部分
	def get_selenium_js_html(self, url):
		browser = webdriver.PhantomJS() 
		browser.get(url) 
		time.sleep(3) 
		#以下两种方式
		# 执行js得到整个页面内容 为什么不行??
		#html = browser.execute_script("return document.documentElement.outerHTML") 

		#直接通过page_source获取网页渲染后的源代码
		html = browser.page_source
		return html

	#获取公众号文章内容
	def parse_wx_articles_by_html(self, selenium_html):
		#以下两种方式
		#beautifulsoup，得到的是list，一块div内容，switch_arctiles_to_list里无法继续搜索，不适用？
		#soup = BeautifulSoup(selenium_html,'html.parser')
		#return soup.select('div[class="weui_media_box appmsg"]')

		#pyquery
		doc = pq(selenium_html)
		print '开始查找内容'
		#有的公众号仅仅有10篇文章，有的可能多一些
		return doc('div[class="weui_media_box appmsg"]')#公众号多余10篇文章的
		#return doc('div[class="weui_msg_card"]')	#公众号只有10篇文章的
 
	#将获取到的文章转换为CSV文件
	def switch_arctiles_to_csv(self, articles):
		#定义变量
		num = []
		date = []
		title = []
		url = []
		summary = []
		list1 = []
		articles_dic = {'num':num,'date': date,'title':title,'url': url,'summary': summary}
		i = 1

		#遍历找到的文章，解析里面的内容
		if articles:
			for article in articles.items():
				self.log(u'开始整合(%d/%d)' % (i, len(articles)))
				#处理单个文章
				list1 = self.parse_one_article(article,i)

				num.append(list1[0])
				date.append(list1[1])
				title.append(list1[2])
				url.append(list1[3])
				summary.append(list1[4])
				i += 1

		#将字典转换为csv文件
		dataframe = pd.DataFrame(articles_dic)
		dataframe.to_csv("gongzhonghao1.csv",index=False,sep=',')

	#解析单篇文章
	def parse_one_article(self, article,i):
		list1 = []
		list2 = []

		#获取标题
		title = article('h4[class="weui_media_title"]').text()
		self.log('标题： %s' % title)
		#获取标题对应的地址
		url = 'http://mp.weixin.qq.com' + article('h4[class="weui_media_title"]').attr('hrefs')
		self.log('地址： %s' % url)
		#获取概要内容
		summary = article('.weui_media_desc').text()
		self.log('文章简述： %s' % summary)
		#获取文章发表时间
		date = article('.weui_media_extra_info').text()
		self.log('发表时间： %s' % date)

		#将这些信息保存成列表数据,返回
		list1 = [i,date,title,url,summary]

		#获取文章文本内容
		r = requests.get(url,headers=self.headers)
		content = r.text
		soup = BeautifulSoup(content,'html.parser')
		texts = soup.select('p')		
		for te in texts:
			list2.append(te.text)

		strilist2 = ','.join(list2)

		#存储文章文本内容到本地
		contentfiletitle=self.keywords+'/'+title+'_'+date+'.txt'
		self.save_content_file(contentfiletitle,strilist2)
		
		return list1

	
	#存储文章到本地	
	def save_content_file(self,title,content):
		#防止有的文章内容被举报或删除了，content为空，加上if判断
		if content:
			with open(title, 'w') as f:
				f.write(content)
		else:
			print '''
			***************************************** 
			**    文章内容不存在       ** 
			*****************************************
			'''
	
	#自定义log函数，主要是加上时间
	def log(self, msg):
		print u'%s: %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), msg)
	
	#验证函数
	def need_verify(self, selenium_html):
		' 有时候对方会封锁ip，这里做一下判断，检测html中是否包含id=verify_change的标签，有的话，代表被重定向了，提醒过一阵子重试 '
		return pq(selenium_html)('#verify_change').text() != ''
	
	#创建公众号命名的文件夹	 为什么不用指定路径，默认放在同路径下？
	def create_dir(self):
		if not os.path.exists(self.keywords):  
			os.makedirs(self.keywords) 
			self.log(u'创建目录成功')
		else:
			
			self.log(u'目录已存在')
	
	#爬虫主函数
	def run(self):
		' 爬虫入口函数 '
		#Step 0 ：  创建公众号命名的文件夹
		self.create_dir()
		
		# Step 1：GET请求到搜狗微信引擎，以微信公众号英文名称作为查询关键字
		self.log(u'开始获取，微信公众号英文名为：%s' % self.keywords)
		self.log(u'开始调用sougou搜索引擎')
		sougou_search_html = self.get_search_result_by_keywords()
		
		# Step 2：从搜索结果页中解析出公众号主页链接
		self.log(u'获取sougou_search_html成功，开始抓取公众号对应的主页wx_url')
		wx_url = self.get_wx_url_by_sougou_search_html(sougou_search_html)
		self.log(u'获取wx_url成功，%s' % wx_url)
				
		# Step 3：Selenium+PhantomJs获取js异步加载渲染后的html
		self.log(u'开始调用selenium渲染html')
		selenium_html = self.get_selenium_js_html(wx_url)
	
		# Step 4: 检测目标网站是否进行了封锁
		if self.need_verify(selenium_html):
			self.log(u'爬虫被目标网站封锁，请稍后再试')
		else:
			# Step 5: 使用PyQuery，从Step 3获取的html中解析出公众号文章列表的数据
			self.log(u'调用selenium渲染html完成，开始解析公众号文章')
			articles = self.parse_wx_articles_by_html(selenium_html)
			self.log(u'抓取到微信文章%d篇' % len(articles))
			
			# Step 6: 把微信文章数据封装成csv文件
			self.log(u'开始整合微信文章数据为csv')
			self.switch_arctiles_to_csv(articles)
			
			self.log(u'保存完成，程序结束')

# main
if __name__ == '__main__':
	print '''
			***************************************** 
			**    Welcome to Spider of 公众号       ** 
			*****************************************
	'''
	gongzhonghao=raw_input(u'输入要爬取的公众号')
	if not gongzhonghao:
		gongzhonghao='iProgrammer'
	weixin_spider(gongzhonghao).run()

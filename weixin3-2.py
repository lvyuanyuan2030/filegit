#!/usr/bin/env python
# coding: utf-8

#程序无法执行：webdriver.Chrome得到的html，用pq方法得到的doc是空的？即不能用pyquery解析，只能用beautifulsoup

#这三行代码是防止在python2上面编码错误的，在python3上面不要要这样设置
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from pyquery import PyQuery as pq

import requests
import os
import sys
import time
import re
import csv


class spider_wechat:

    def __init__(self, name,url):
        self.keywords = name
        self.url = url
        self.old_scroll_height = 0
        # 爬虫伪装头部设置
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0'}

    #使用webdriver加载公众号主页内容，主要是js渲染的部分，一直加载滚动条至结束
    def get_selenium_js_html(self):
        # Chromedriver
        opt = webdriver.ChromeOptions()
        opt.add_argument('Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 MicroMessenger/6.5.2.501 NetType/WIFI WindowsWechat QBCore/3.43.884.400 QQBrowser/9.0.2524.400')#设置headers
        driver = webdriver.Chrome(chrome_options=opt)
        driver.get(self.url)
        time.sleep(10)
        top = 1
        #for i in range(3):
        tags1 = BeautifulSoup(driver.page_source,'html.parser').find('div',id='js_nomore')
        if tags1:
            if(tags1.get('style')) == 'display: none;':
                #js = "var q=document.documentElement.scrollTop="+str(top*2000)
                #driver.execute_script(js)#模拟下滑操作
                top += 1
                time.sleep(3) 
            else:
                print 'url timeout'
        return driver.page_source


    #获取文章内容
    def parse_wx_articles_by_html(self, selenium_html):
        #soup = BeautifulSoup(selenium_html,'html.parser')
        #return soup.select('div[class="weui_media_box appmsg js_appmsg"]')
        doc = pq(selenium_html)
        return doc('div[class="weui_media_box appmsg js_appmsg"]')


    #将获取到的文章转换为字典，并向csv文件写入行
    def switch_arctiles_to_list(self,articles,writer):
        #定义存贮变量
        i = 1

        #遍历找到的文章，解析里面的内容
        if articles:
            for article in articles.items():
                self.log(u'开始解析文章(%d/%d)' % (i, len(articles)))
                #处理单个文章
                self.parse_one_article(article,i,writer)
                i += 1


    #解析单篇文章
    def parse_one_article(self, article,i,writer):
        list1 = []
        #获取标题
        title = article('h4[class="weui_media_title"]').text()
        self.log('标题： %s' % title)
        #获取标题对应的地址
        url = article('h4[class="weui_media_title"]').attr('hrefs')
        self.log('地址： %s' % url)
        #获取概要内容
        summary = article('.weui_media_desc').text()
        self.log('文章简述： %s' % summary)
        #获取文章发表时间
        date = article('.weui_media_extra_info').text()
        self.log('发表时间： %s' % date)

        #获取文章文本内容
        r = requests.get(url,headers=self.headers)
        content = r.text
        soup = BeautifulSoup(content,'html.parser')
        texts = soup.select('p')        
        for te in texts:
            list1.append(te.text)
        strilist = ','.join(list1)

        #存储文章文本内容到本地
        contentfiletitle=title+'_'+date+'.txt'
        self.save_content_file(contentfiletitle,strilist)
        
        #csv文件增加行
        csvfiletitle = self.keywords+'.csv'
        with open(csvfiletitle,"a") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([i,date,title,url,summary])


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


    #存贮csv数据到本地
    def save_csvfile(self):
        csvfiletitle = self.keywords+'.csv'
        with open(csvfiletitle,"w") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([u'编号',u'时间',u'文章标题',u'文章地址',u'文章简介'])
            return writer
    
    #自定义log函数，主要是加上时间
    def log(self, msg):
        print u'%s: %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), msg)
    
    #验证函数
    def need_verify(self, selenium_html):
        #有时候对方会封锁ip，这里做一下判断，检测html中是否包含id=verify_change的标签，有的话，代表被重定向了，提醒过一阵子重试
        return pq(selenium_html)('#verify_change').text() != ''
    
    #创建公众号命名的文件夹 不用指定路径，默认在python存放路径
    def create_dir(self):
        if not os.path.exists(self.keywords):  
            os.makedirs(self.keywords) 
            self.log(u'创建公众号目录成功')
        else:
            
            self.log(u'公众号目录已存在')

    #爬虫主函数
    def run(self):
        #Step 0 ：  创建公众号命名的文件夹，创建csv文件
        self.create_dir()
        writer = self.save_csvfile()

        # Step 1：Selenium+PhantomJs获取js异步加载渲染后的html
        selenium_html = self.get_selenium_js_html()
        print selenium_html

        # Step 2: 检测目标网站是否进行了封锁
        if self.need_verify(selenium_html):
            self.log(u'爬虫被目标网站封锁，请稍后再试')
        else:
            # Step 3: 使用PyQuery，从html中解析出公众号文章列表的数据
            self.log(u'公众号历史消息入口html渲染完成，开始解析公众号所有历史文章')
            articles = self.parse_wx_articles_by_html(selenium_html)
            self.log(u'抓取到历史文章%d篇' % len(articles))
            print articles
            # Step 4: 把微信文章数据存储为csv文件
            self.switch_arctiles_to_list(articles,writer)
            
            self.log(u'保存完成，程序结束')
		

if __name__ == '__main__':
    print '''
            ***************************************** 
            **    Welcome to Spider of 公众号       ** 
            *****************************************
    '''
    wechat_name = raw_input(u'输入要爬取的公众号name')
    wechat_url = raw_input(u'输入要爬取的公众号历史消息地址url')

    #判断url格式是否合法，若合法再继续
    if re.match(r'^https?:/{2}\w.+$', wechat_url):
        wechat = spider_wechat(wechat_name,wechat_url)
        wechat.run()
    else:
        print 'url error!'

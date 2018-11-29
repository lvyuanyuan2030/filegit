# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class IpcrawlerItem(scrapy.Item):
    # define the fields for your item here like:
    ID = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    ICP = scrapy.Field()
    main_text = scrapy.Field()
    next_urls = scrapy.Field()
    maxnum_nexturls = scrapy.Field()
    

class IpNextcrawlerItem(scrapy.Item):
	num_url = scrapy.Field()
	maxnum_urls = scrapy.Field()
	last_ID = scrapy.Field()
	next_ID = scrapy.Field()
	next_text = scrapy.Field()
	all_text = scrapy.Field()
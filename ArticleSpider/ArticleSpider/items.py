# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import datetime
import re
import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose, TakeFirst, Join
from w3lib.html import remove_tags
from models.es_types import ArticleType
from elasticsearch_dsl.connections import connections
es = connections.create_connection(ArticleType._doc_type.using)

# def date_convert(value):
#     try:
#         create_date = datetime.datetime.strptime(value, "%Y/%m/%d").date()
#     except Exception as e:
#         create_date = datetime.datetime.now().date()
#
#     return create_date
#
#
# def get_nums(value):
#     match_re = re.match(".*?(\d+).*", value)
#     if match_re:
#         nums = int(match_re.group(1))
#     else:
#         nums = 0
#     return nums
#
#
# def remove_comment_tags(value):
#     #去掉tag中提取的评论
#     if "评论" in value:
#         return ""
#     else:
#         return value
#
#
# def return_value(value):
#     return value

def gen_suggests(index, info_tuple):
    #根据字符串生成搜索建议数组
    used_words = set()
    suggests = []
    for text, weight in info_tuple:
        if text:
            #调用es的analyze接口分析字符串
            words = es.indices.analyze(index=index, analyzer="ik_max_word", params={'filter':["lowercase"]}, body=text)
            anylyzed_words = set([r["token"] for r in words["tokens"] if len(r["token"])>1])
            new_words = anylyzed_words - used_words
        else:
            new_words = set()

        if new_words:
            suggests.append({"input":list(new_words), "weight":weight})

    return suggests


#由于每一个结果都是去第一个值，每个值全部调用这个方法重复代码过多，所以可以自定义ArticleItemLoader解决
# class ArticleItemLoader(ItemLoader):
#     #自定义itemloader
#     default_output_processor = TakeFirst()


class JobBoleArticleItem(scrapy.Item):
    print("-------------do items------------")
    title = scrapy.Field()
    create_date = scrapy.Field(
       #input_processor=MapCompose(date_convert),
    )
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    front_image_url = scrapy.Field(
       #output_processor=MapCompose(return_value)
    )
    front_image_path = scrapy.Field()
    praise_nums = scrapy.Field(
      # input_processor=MapCompose(get_nums)
    )
    comment_nums = scrapy.Field(
        #input_processor=MapCompose(get_nums)
    )
    fav_nums = scrapy.Field(
       # input_processor=MapCompose(get_nums)
    )
    tags = scrapy.Field(
      # input_processor=MapCompose(remove_comment_tags),
      # output_processor=Join(",")
    )
    content = scrapy.Field(
       #input_processor=MapCompose(remove_tags)
    )
    print("-----------item succeed-------------")





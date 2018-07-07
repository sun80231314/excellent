# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import codecs
import json
from scrapy.pipelines.images import ImagesPipeline
from twisted.enterprise import adbapi
from models.es_types import ArticleType
from w3lib.html import remove_tags
import MySQLdb
import MySQLdb.cursors
from items import gen_suggests


# class ArticlespiderPipeline(object):
#     def process_item(self, item, spider):
#         return item


class JsonWithEncodingPipeline(object):
    #自定义json文件的导出
    def __init__(self):
        self.file = codecs.open('article.json', 'wb+', encoding="utf-8")
    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(lines)
        return item
    def spider_closed(self, spider):
        self.file.close()


class MysqlPipeline(object):
    #采用同步的机制写入mysql
    def __init__(self):
        self.conn = MySQLdb.connect('localhost', 'root', 'root', 'article_spider', charset="utf8", use_unicode=True)
        self.cursor = self.conn.cursor()
    print("---------do insert -----------")
    def process_item(self, item, spider):
        insert_sql = """
                   insert into jobbole_article(title, url, url_object_id,create_date, fav_nums, front_image_url, front_image_path,
                   praise_nums, comment_nums, tags, content)
                   VALUES (%s, %s, %s,%s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE fav_nums=VALUES(fav_nums),praise_nums=VALUES(praise_nums),comment_nums=VALUES(comment_nums)
               """
        try:
            self.cursor.execute(insert_sql, (item["title"], item["url"], item["url_object_id"], item["create_date"], item["fav_nums"], item["front_image_url"],
                                         item["front_image_path"], item["praise_nums"], item["comment_nums"], item["tags"], item["content"]))
            self.conn.commit()
        except Exception as e:
            print("错误是:")
            print(e)

    print("--------- insert did -----------")

#
class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        #比如有的网站没有封面图，所以要做一个判断
        if "front_image_url" in item:
            for ok, value in results:
                image_file_path = value["path"]
            item["front_image_path"] = image_file_path

        return item



class ElasticsearchPipeline(object):
    #将数据写入到es中
    def process_item(self, item, spider):
        #将item转换为es的数据
        article = ArticleType()
        article.title = item['title']
        article.create_date = item["create_date"]
        article.content = remove_tags(item["content"])
        article.front_image_url = item["front_image_url"]
        if "front_image_path" in item:
            article.front_image_path = item["front_image_path"]
        article.praise_nums = item["praise_nums"]
        article.fav_nums = item["fav_nums"]
        article.comment_nums = item["comment_nums"]
        article.url = item["url"]
        article.tags = item["tags"]
        article.meta.id = item["url_object_id"]
        article.suggest = gen_suggests(ArticleType._doc_type.index, ((article.title, 10), (article.tags, 7)))
        article.save()
        return item
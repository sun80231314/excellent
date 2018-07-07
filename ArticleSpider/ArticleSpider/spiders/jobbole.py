# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request
from urllib import parse
from ArticleSpider.items import JobBoleArticleItem, ArticleItemLoader
from ArticleSpider.utils.common import get_md5
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
import re
import datetime

class JobboleSpider(scrapy.Spider):
    name = "jobbole"
    allowed_domains = ["blog.jobbole.com"]
    start_urls = ['http://blog.jobbole.com/all-posts']

    def parse(self, response):
        # 解析列表页中的所有文章url并交给scrapy下载后并进行解析
        #post_nodes = response.css("#archive .floated-thumb .post-thumb a")
        post_nodes = response.xpath('//div[@class="post floated-thumb"]/div[@class="post-thumb"]//a')
        for post_node in post_nodes:
            # image_url = post_node.css("img::attr(src)").extract_first("")
            # post_url = post_node.css("::attr(href)").extract_first("")
            post_url = post_node.xpath('@href').extract_first("")
            image_url = post_node.xpath('img/@src').extract_first("")
            # post_url 是我们每一页的具体的文章url。
            # 下面这个request是文章详情页面. 使用回调函数每下载完一篇就callback进行这一篇的具体解析。
            # 我们现在获取到的是完整的地址可以直接进行调用。如果不是完整地址: 根据response.url + post_url
            # def urljoin(base, url)完成url的拼接
            # 初始化好的Request如何交给scrapy进行下载: yield关键字
            yield Request(url=parse.urljoin(response.url, post_url), meta={"front_image_url":image_url}, callback=self.parse_detail)
        #提取下一页并交给scrapy进行下载
        next_url = response.css(".next.page-numbers::attr(href)").extract_first("")
        # 如果.next .pagenumber 是指两个class为层级关系。而不加空格为同一个标签
        if next_url:
            yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)

            #yield和return的区别: yield生成值并不会中止程序的执行，返回值后程序继续往后执行，return返回值后，程序将中止执行


    def parse_detail(self, response):
        article_item = JobBoleArticleItem()
        front_image_url = response.meta.get("front_image_url", "")
        title = response.xpath('//div[@class="entry-header"]/h1/text()').extract_first("")
        try:
           create_date = response.xpath("//p[@class='entry-meta-hide-on-mobile']/text()").extract()[0].strip().replace("·","").strip()
        except Exception as e:
           print(e)
        praise_nums = response.xpath("//span[contains(@class, 'vote-post-up')]/h10/text()").extract()[0]
        match_re = re.match(".*?(\d+).*", praise_nums)
        if match_re:
            praise_nums = match_re.group(1)
        else:
            praise_nums = 0
        fav_nums = response.xpath("//span[contains(@class, 'bookmark-btn')]/text()").extract()[0]
        match_re = re.match(".*?(\d+).*", fav_nums)
        if match_re:
            fav_nums = match_re.group(1)
        else:
            fav_nums = 0
        comment_nums = response.xpath("//a[@href='#article-comment']/span/text()").extract()[0]
        match_re = re.match(".*?(\d+).*", comment_nums)
        if match_re:
            comment_nums = match_re.group(1)
        else:
            comment_nums = 0
        content = response.xpath("//div[@class='entry']").extract()[0]
        tag_list = response.xpath("//p[@class='entry-meta-hide-on-mobile']/a/text()").extract()
        tag_list = [element for element in tag_list if not element.strip().endswith("评论")]
        tags = ",".join(tag_list)
        print("-------------kaishi ------------")
        article_item["url_object_id"] = get_md5(response.url)
        article_item["title"] = title
        article_item["url"] = response.url
        try:
            create_date = datetime.datetime.strptime(create_date, "%Y/%m/%d").date()
        except Exception as e:
            create_date = datetime.datetime.now().date()
        article_item["create_date"] = create_date
        article_item["front_image_url"] = [front_image_url]
        article_item["praise_nums"] = praise_nums
        article_item["comment_nums"] = comment_nums
        article_item["fav_nums"] = fav_nums
        article_item["tags"] = tags
        article_item["content"] = content
        yield article_item

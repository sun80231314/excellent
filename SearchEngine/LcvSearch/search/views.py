#coding=utf-8
import redis
from django.shortcuts import render
from django.views.generic.base import View
from elasticsearch import Elasticsearch
from datetime import datetime
from search.models import JobboleType
from django.http import HttpResponse
import json

# es客户端
client = Elasticsearch(hosts=["localhost"])


class SearchSuggest(View):
    def get(self, request):
        key_words = request.GET.get('s','')
        re_datas = []
        if key_words:
            s = JobboleType.search()
            s = s.suggest('my_suggest', key_words, completion={
                "field":"suggest",
                   "fuzzy":{
                       "fuzziness":2
                },
                "size": 5
            })
            suggestions = s.execute_suggest()
            for match in suggestions.my_suggest[0].options:
                source = match._source
                re_datas.append(source["title"])
        return HttpResponse(json.dumps(re_datas), content_type="application/json")


# 搜索结果页
class SearchView(View):
    # 处理get请求
    @staticmethod
    def get(request):
        # 获取搜索参数
        key_words = request.GET.get("q", "")

        # 获取页数
        page = request.GET.get("p", "1")
        try:
            # 将获取的页面参数转型为整数
            page = int(page)
        except:
            # 若转型失败，默认为1
            page = 1
        # 开始查询时间
        start_time = datetime.now()
        # 开始es查询
        response = client.search(
            index="jobbole",
            # 查询体
            body={
                "query": {
                    "multi_match": {
                        "query": key_words,# 查询参数
                        "fields": ["tags", "title", "content"]
                    }
                },
                # 查询开始下标
                "from": (page - 1) * 10,
                # 查询总数
                "size": 10,
                # 高亮及包装字体
                "highlight": {
                    # 关键字前的包装html
                    "pre_tags": ['<span class="keyWord">'],
                    # 关键字后的包装html
                    "post_tags": ["</span>"],
                    "fields": {
                        "title": {},
                        "content": {}
                    }
                }
            }
        )
        end_time = datetime.now()
        last_seconds = (end_time - start_time).total_seconds()
        # 获取查询返回结果总数
        total_nums = response["hits"]["total"]
        if (page % 10) > 0:
            page_nums = int(total_nums / 10) + 1
        else:
            page_nums = int(total_nums / 10)
        # 查询结果包装
        hit_list = []
        for hit in response["hits"]["hits"]:
            hit_dict = {}
            # 标题-判断本条查询结果是否是带查询参数，如果带，则使用高亮字体，否则使用普通文本
            if "highlight" in hit and "title" in hit["highlight"]:
                hit_dict["title"] = "".join(hit["highlight"]["title"])
            else:
                hit_dict["title"] = "".join(hit["_source"]["title"])
            # 内容-判断本条查询结果是否是带查询参数，如果带，则使用高亮字体，否则使用普通文本
            if "highlight" in hit and "content" in hit["highlight"]:
                # :500是截取500个字符 最后拼接</span> 是为了防止前面截取的字符串导致span没有争取结束而格式混乱
                hit_dict["content"] = "".join(hit["highlight"]["content"])[:500]+"</span>"
            else:
                hit_dict["content"] = "".join(hit["_source"]["content"])[:500]+"</span>"

            hit_dict["create_date"] = hit["_source"]["create_date"]
            hit_dict["url"] = hit["_source"]["url"]
            hit_dict["score"] = hit["_score"]
            hit_list.append(hit_dict)
        return render(request, "result.html", {"page": page,
                                               "total_nums": total_nums,
                                               "all_this": hit_list,
                                               "key_words": key_words,
                                               "page_nums": page_nums,
                                               "last_seconds": last_seconds})

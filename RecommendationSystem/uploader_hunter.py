# -*- coding: utf-8 -*-
# author:And370
# time:2021/2/3

import random
import json
import time
import requests
import pandas as pd

pd.options.display.max_columns = None


def str_to_dict(x):
    return eval('{"' + x.replace(": ", '":"').replace('\n', '","') + '"}')


headers = str_to_dict("""accept: */*
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
referer: https://space.bilibili.com/6574487/fans/follow
sec-fetch-dest: script
sec-fetch-mode: no-cors
sec-fetch-site: same-site
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36""")


# 获取单个UP主的关注对象
def follows_spider(up_id):
    data = []
    page = 1
    # B站默认限制查看前100个关注者
    while page <= 5:
        print(up_id, page)
        # 关注者api
        api_url = "http://api.bilibili.com/x/relation/followings?vmid=%s&pn=%s&ps=20&order=desc&jsonp=jsonp&callback=__jp5" % (
            up_id, page)
        response = requests.get(api_url, headers=headers)

        try:
            # 关注者
            follows = json.loads(response.text[6:-1])["data"]["list"]
        except Exception as e:
            print(e)
            print(json.loads(response.text[6:-1]))
        if not follows:
            break

        data.extend(follows)
        page += 1

        time.sleep(random.randint(5, 12) * 0.1)
    return data


# BFS
# 广度优先搜索UP主的关注对象
def follow_tree_spider(seeds, deep=1):
    # 详细数据
    final_data = pd.DataFrame()
    # 已获取
    from_cache = set()
    # 待获取
    queue = set(seeds)

    for i in range(deep):
        sub_data = pd.DataFrame()
        for seed in queue:
            sub_data = pd.DataFrame(follows_spider(seed))
            sub_data["from"] = seed
            final_data = final_data.append(sub_data)
        # 单层搜索结束进行缓存更新
        from_cache.update(queue)
        # 当前列表去除缓存数据
        # print(sub_data.columns)
        queue = set(sub_data["mid"]) - from_cache
        # 数据汇总
    return final_data


if __name__ == '__main__':
    seeds = ['6574487']
    data = follow_tree_spider(seeds, 5)
    data.to_excel("./data/follows_deep5.xlsx",index=False)

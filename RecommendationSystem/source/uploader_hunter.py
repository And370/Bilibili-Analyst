# -*- coding: utf-8 -*-
# author:And370
# time:2021/2/3

import os
import random
import json
import time
import requests

import pandas as pd

from ast import literal_eval
from tqdm import tqdm

pd.options.display.max_columns = None


class Follows(object):
    def __init__(self, seeds, csv_path, per_page, order="desc"):
        """
        :param seeds: 种子用户ID
        :param csv_path: 历史文件
        :param per_page: 每页的数量 [1,50]
        :param order: ["desc","asc","both"],desc最新关注,asc最早关注,both双侧
        """

        self.seeds = seeds

        self.csv_path = csv_path
        self.raw_data = pd.read_csv(csv_path, encoding="utf_8_sig") if os.path.exists(csv_path) else None

        self.per_page = per_page
        self.order = [order] if order in ["desc", "asc"] else ["desc", "asc"]
        self.history = set(self.raw_data["from"].astype(int)) if isinstance(self.raw_data, pd.DataFrame) else set()

        self.headers = {'accept': '*/*',
                        'accept-encoding': 'gzip, deflate, br',
                        'accept-language': 'zh-CN,zh;q=0.9',
                        'referer': 'https://space.bilibili.com/xxx/fans/follow',
                        'sec-fetch-dest': 'script',
                        'sec-fetch-mode': 'no-cors',
                        'sec-fetch-site': 'same-site',
                        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36'}

    @staticmethod
    def headers_format(raw_headers):
        return literal_eval('{"' + raw_headers.replace(": ", '":"').replace('\n', '","') + '"}')

    # 获取单个UP主的关注对象
    def follows(self, up_id):
        data = []
        page = 1
        self.headers["referer"] = 'https://space.bilibili.com/%s/fans/follow' % up_id
        # B站默认限制查看前100个关注者
        while page <= 5:
            # print(up_id, page)
            for order in self.order:
                time.sleep(random.randint(5, 12) * 0.1)
                # 关注者api
                api_url = "http://api.bilibili.com/x/relation/followings?vmid=%s&pn=%s&ps=%s&order=%s&jsonp=jsonp&callback=__jp5" % (
                    up_id, page, self.per_page, order)
                response = requests.get(api_url, headers=self.headers)

                try:
                    # 关注者
                    follows = json.loads(response.text[6:-1])["data"]["list"]
                    if not follows:
                        continue
                    data.extend(follows)
                except Exception as e:
                    print(e)
                    print(response.text)
                    # print(json.loads(response.text[6:-1]))
            page += 1

        return data

    # BFS
    # 广度优先搜索UP主的关注对象
    def follow_tree(self, seeds=None, deep=1):
        # 待获取
        queue = set(seeds) if seeds else self.seeds

        for i in range(deep):
            sub_data = pd.DataFrame()
            for seed in tqdm(queue):
                sub_data = pd.DataFrame(self.follows(seed))
                sub_data["from"] = seed
                sub_data.to_csv(self.csv_path,
                                header=False,
                                index=False,
                                mode="a",
                                encoding="utf_8_sig")
                # final_data = final_data.append(sub_data)
            # 单层搜索结束进行缓存更新
            self.history.update(queue)
            # 当前列表去除缓存数据
            queue = set(sub_data["mid"]) - self.history
        return

    def cache_load(self, history):
        self.history.update(set(history))


if __name__ == '__main__':
    path = "../data/user2up.csv"
    dt = pd.read_csv(path, encoding="utf_8_sig")
    seeds = set(dt["mid"].astype(int)) - set(dt["from"].astype(int))
    follows = Follows(seeds, path, 20, "both")
    follows.follow_tree(deep=3)

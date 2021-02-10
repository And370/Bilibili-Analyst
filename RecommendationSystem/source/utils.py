# !/usr/bin/env python
# -*- coding: utf-8 -*-
# author:And370
# time:2021/2/10

from itertools import combinations, chain
from tqdm import tqdm
import pandas as pd


class UserCF(object):
    def __init__(self, df_user2item: pd.DataFrame, user: str, item: str, K: int, N: int):
        for col in [user, item]:
            if col not in df_user2item.columns:
                raise Exception("%s is not in columns." % col)
        self.user_name = user
        self.item_name = item
        self.df = df_user2item[[user, item]].astype(int)
        self.users = self.df[user].unique()
        self.items = self.df[item].unique()
        # 基于topK相似user推荐topN的item
        self.K = K
        self.N = N

        # user-item双向矩阵
        self.user2item_n = self.df.groupby(user).agg(list)
        self.item2user_n = self.df.groupby(item).agg(list)

        # user-user矩阵
        self.user2user_n = pd.DataFrame(columns=self.users, index=self.users, data=0)
        self._user2user_n()

        # user-user相似度矩阵
        self.user2user_sim = pd.DataFrame(columns=self.users, index=self.users, data=0)
        self._user2user_sim()

        # 兴趣度
        self.interest_cache = {}

        self.user2user_sim_rank = self.user2user_sim.rank(ascending=False, method="max").astype(int)
        self.user2item_KN = pd.DataFrame()
        self.cache_KN = {}

        self._recommend(K, N)

    def _user2user_n(self):
        """
        生成user相交矩阵
        """
        for up, user in tqdm(zip(self.item2user_n.index, self.item2user_n.user)):
            for i, j in combinations(user, 2):
                self.user2user_n.loc[i, j] += 1
                self.user2user_n.loc[j, i] += 1

    def _jaccard(self, user_a, user_b):
        """jaccard相似度"""
        return 0 if not self.user2user_n.loc[user_a, user_b] \
            else self.user2user_n[user_a][user_b] / \
                 len(set(self.user2item_n["up"][user_a]) | set(self.user2item_n["up"][user_b]))

    def _user2user_sim(self):
        """user间相似度"""
        for user_a, user_b in tqdm(combinations(self.users, 2)):
            # 注意这里,pandas很容易忽略的一个引用问题
            self.user2user_sim.loc[user_a, user_b] = self.user2user_sim.loc[user_b,user_a] = self._jaccard(user_a, user_b)

    def _interest_user2item(self, user, item):
        """user-item兴趣度"""
        cache_value = self.interest_cache.get((user, item))
        if cache_value:
            return cache_value

        interest = 0
        for other_user in self.item2user_n.loc[item, self.user_name]:
            interest += self.user2user_sim.loc[user, other_user]
        self.interest_cache[(user, item)] = interest
        return interest

    def _recommend(self, K, N):
        self.user2item_KN["topK_user"] = self.user2user_sim_rank.apply(lambda x: list(x[x < N].index), axis=1)
        self.user2item_KN["topK_user_len"] = self.user2item_KN["topK_user"].apply(len)
        self.user2item_KN["topK_user_all_items"] = self.user2item_KN["topK_user"].apply(
            lambda x: list(chain(*self.user2item_n.loc[x, self.item_name])))
        self.user2item_KN["topK_user_all_items_len"] = self.user2item_KN["topK_user_all_items"].apply(len)
        self.user2item_KN["interests"] = self.user2item_KN.apply(
            lambda x: {up: self._interest_user2item(x.name, up) for up in x.topK_user_all_items}, axis=1)
        self.user2item_KN["topK_interests"] = self.user2item_KN.apply(
            lambda x: sorted(x.interests.items(), key=lambda item: item[1], reverse=True)[:10], axis=1)
        self.user2item_KN["topK_item"] = self.user2item_KN["topK_interests"].apply(lambda x: [i[0] for i in x])
        self.cache_KN[(K, N)] = self.user2item_KN.copy()

    def recommend(self, user):
        return self.user2item_KN.loc[user, "topK_item"]

    def change_KN(self, K, N):
        self.K = K
        self.N = N
        self.user2item_KN = self.cache_KN.get((K, N))
        if not self.user2item_KN:
            self._recommend(K, N)

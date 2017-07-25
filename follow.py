#!/usr/bin/env python
# encoding: utf-8

"""
@author: wangyongxu
@software: PyCharm
@file: zhiboReminder.py
@time: 2017/7/13 下午3:11
"""
import datetime
import requests
from pymongo import MongoClient
from bson.objectid import ObjectId
import time
from settings import MONGO_DB_PWD

mongodb_url = 'mongodb://chaos:{0}@115.159.180.114/zhiboReminder'.format(MONGO_DB_PWD)
mongodb = MongoClient(mongodb_url)
db = mongodb['zhiboReminder']


class Follow(object):
    def __init__(self):
        self.mongodb_url = 'mongodb://chaos:{0}@115.159.180.114/zhiboReminder'.format(MONGO_DB_PWD)

    def all_followed_liver_id(self):
        """
        获得所有关注的主播
        :return:
        """
        try:
            mongo_db = MongoClient(self.mongodb_url)
            db = mongo_db['zhiboReminder']
            follow_lists = db['followlists']
            follow_lists_q = follow_lists.find()
            if follow_lists_q:
                all_liver_id = [live_id for livers in follow_lists_q for live_id in livers.get('roomid')]
            all_liver_id = set(all_liver_id)
            # print len(all_liver_id), all_liver_id
            return all_liver_id
        except Exception, e:
            print e

    def is_living(self, roomid):
        """
        主播是否正在直播
        :return: room_status 1表示开播，2表示未开播
        """
        url = 'http://open.douyucdn.cn/api/RoomApi/room/{0}'.format(roomid)
        rsp = requests.get(url=url)
        if rsp.json().get('error') == 0:
            return rsp.json().get('data').get('room_status')

    def all_living_state(self):
        """
        所有主播状态
        :return:
        """
        lives_state = []
        for roomid in self.all_followed_liver_id():
            d = {
                'roomid': roomid,
                'room_status': self.is_living(roomid=roomid)
            }
            lives_state.append(d)
            print "主播状态，网络请求", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            time.sleep(1)
        print lives_state
        return lives_state

    def uid_list(self):
        """
        :return: list
        such as:{'follower': [u'5956aa246fb5066caf99ba19'], 'roomid': u'652458'}
        返回所有正在主播的人和关注者id
        """
        mongo_db = MongoClient(self.mongodb_url)
        db = mongo_db['zhiboReminder']
        follow_lists = db['followlists']
        living_and_follower = []
        for live in self.all_living_state():
            if live.get('room_status') == '1':
                roomid = live.get('roomid')
                follow_uid_dict = follow_lists.find({'roomid': roomid})
                d = {
                    'roomid': roomid,
                    'follower': [i.get('token') for i in follow_uid_dict]
                }
                living_and_follower.append(d)
        print living_and_follower
        return living_and_follower

    def update_roomid_state(self):
        """
        升级房间状态：
           now_status | last_status
          本次请求的状态 | 上次请求时状态
                1     |     1           =>  正在直播中，不再推送
                1     |     2           =>  刚开播，推送（状态变化）
                2     |     1           =>  刚关播，不推送（状态变化）
                2     |     2           =>  一直关播，不推送

        :return:
        """
        mongo_db = MongoClient(self.mongodb_url)
        db = mongo_db['zhiboReminder']
        roomid_status = db['roomid_status']
        for live_status in self.all_living_state():
            key = {'roomid': live_status.get('roomid')}
            r = roomid_status.find_one(key)
            # if live_status.get('roomid') == '564697':
            #     print live_status
            print 'roomid_status:', r
            if r:
                update_para = {
                    'roomid': r.get('roomid'),
                    'last_status': r.get('now_status'),
                    'now_status': live_status.get('room_status')
                }
                roomid_status.update(key, update_para)
            else:
                update_para = {
                    'roomid': live_status.get('roomid'),
                    'last_status': '2',
                    'now_status': '2'
                }
                roomid_status.insert(update_para)

    def conn_mongodb(self):
        return MongoClient(self.mongodb_url)



def follower2token(uid_list):
    follow = Follow()
    mongo_db = follow.conn_mongodb()
    db = mongo_db['zhiboReminder']
    users = db['users']
    tokens = []
    for uid in uid_list:
        if users.find_one({'_id': ObjectId(uid)}):
            deviceTokens = users.find_one({'_id': ObjectId(uid)}).get('deviceTokens')
            if deviceTokens:
                tokens.extend(deviceTokens)
    return tokens


if __name__ == '__main__':
    follow = Follow()
    follow.update_roomid_state()
    print '更新主播状态成功:', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    time.sleep(900)



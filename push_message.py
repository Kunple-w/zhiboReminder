#!/usr/bin/env python
# encoding: utf-8

"""
@author: wangyongxu
@software: PyCharm
@file: zhiboReminder.py
@time: 2017/7/13 下午3:11
"""
import datetime

from apns import APNs, Frame, Payload, PayloadAlert
import time
import requests

from follow import Follow, follower2token


def push_message(deviceToken, title=None, subtitle=None, body=None):
    apns = APNs(use_sandbox=True, cert_file='./public.pem', key_file='./private.pem.unsecure')

    alert = PayloadAlert(title=title, subtitle=subtitle, body=body)
    payload = Payload(alert=alert, sound="default", badge=1, category='saySomething',
                      custom={"name": "Chaos", "img": "http://easyulife-1253741099.cossh.myqcloud.com/123.jpg"},
                      mutable_content=True)

    apns.gateway_server.send_notification_multiple()


def push_multi_messages(roomid, tokens):
    apns = APNs(use_sandbox=True, cert_file='./public.pem', key_file='./private.pem.unsecure')
    roominfo = room_info(roomid)
    kwargs = {
        'title': roominfo.get('owner_name') + roominfo.get('start_time'),
        'body': roominfo.get('room_name')
    }
    alert = PayloadAlert(**kwargs)
    payload = Payload(alert=alert, sound="default", badge=1, category='saySomething',
                      custom={"roomid": roomid, "img": roominfo.get('room_thumb')},
                      mutable_content=True)
    frame = Frame()
    identifier = 1
    expiry = time.time() + 3600
    priority = 10
    if tokens:
        for token in tokens:
            frame.add_item(token, payload, identifier, expiry, priority)
            print 'token', token
        apns.gateway_server.send_notification_multiple(frame=frame)


def room_info(roomid):
    url = 'http://open.douyucdn.cn/api/RoomApi/room/{0}'.format(roomid)
    rsp = requests.get(url=url)
    if rsp.json().get('error') == 0:
        kwrags = {
            'room_thumb': rsp.json().get('data').get('room_thumb'),
            'room_name': rsp.json().get('data').get('room_name'),
            'room_id': rsp.json().get('data').get('room_id'),
            'owner_name': rsp.json().get('data').get('owner_name'),
            'start_time': rsp.json().get('data').get('start_time'),
        }
        return kwrags


def push_to_client():
    """
    推送主播状态到客户端
    :return:
    """
    follow = Follow()
    mongo_db = follow.conn_mongodb()
    db = mongo_db['zhiboReminder']
    roomid_status = db['roomid_status']
    for uid_roomid in follow.uid_list():
        roomid = uid_roomid.get('roomid')
        uid_list = uid_roomid.get('follower')
        k = {'roomid': roomid}
        r_status = roomid_status.find_one(k)
        if r_status:
            if r_status.get('last_status') == '2' and r_status.get('now_status') == '1':
                # if roomid == '564697':
                print type(follower2token(uid_list)), follower2token(uid_list)
                push_multi_messages(roomid, follower2token(uid_list))


if __name__ == '__main__':
    # tokens = [u'd38e4ac2a1931d5c0ca05ecd4294609a7771404569f8578f4f7402dc5bd0c615', u'f1719af3f0ab87373518565646c710c90131e06e8c60925df9de75addd12fa53']
    # push_multi_messages(tokens)
    push_to_client()
    print '消息推送成功:', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    time.sleep(900)

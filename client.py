#!/usr/bin/env python
# encoding: utf-8
"""
@author: wicki
@contact: gzswicki@gmail.com
@date: 17/1/1
"""

import os
import requests
import re
import time
import xml.dom.minidom
import json
import sys
import ssl
import random
import thread
import model


class WeChatClient:
    def __init__(self, session_id):
        self.session_id = session_id
        self.tip = 0
        self.uuid = ''

        self.base_uri = ''
        self.redirect_uri = ''
        self.push_uri = ''

        self.skey = ''
        self.wxsid = ''
        self.wxuin = ''
        self.pass_ticket = ''
        self.deviceId = 'wxeb7ec651dd0aefa9'
        self.BaseRequest = {}
        self.ContactList = []
        self.MemberList = []
        self.StrangerList = []
        self.My = []
        self.SyncKey = []
        self.member_count = 0
        self.unstar_member_count=0

        if not os.path.exists('static/img/qrcode'):
            os.mkdir('static/img/qrcode')
        if not os.path.exists('static/img/avatar'):
            os.mkdir('static/img/avatar')
        self.qrcode = 'static/img/qrcode/' + self.session_id + ".jpg"

        if hasattr(ssl, '_create_unverified_context'):
            ssl._create_default_https_context = ssl._create_unverified_context

        headers = {
            'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.125 Safari/537.36'}
        self.myRequests = requests.Session()
        self.myRequests.headers.update(headers)

    def responseState(self, func, BaseResponse):
        ErrMsg = BaseResponse['ErrMsg']
        Ret = BaseResponse['Ret']

        if Ret != 0:
            print 'func: %s, Ret: %d, ErrMsg: %s' % (func, Ret, ErrMsg)
            return False
        return True

    def getUUID(self):
        global uuid

        url = 'https://login.weixin.qq.com/jslogin'
        params = {
            'appid': 'wx782c26e4c19acffb',
            'fun': 'new',
            'lang': 'zh_CN',
            '_': int(time.time()),
        }

        r = self.myRequests.get(url=url, params=params)
        r.encoding = 'utf-8'
        data = r.text

        # print(data)

        # window.QRLogin.code = 200; window.QRLogin.uuid = "oZwt_bFfRg==";
        regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"'
        pm = re.search(regx, data)

        code = pm.group(1)
        self.uuid = pm.group(2)

        if code == '200':
            return True

        return False

    def getQRImage(self):
        url = 'https://login.weixin.qq.com/qrcode/' + self.uuid
        params = {
            't': 'webwx',
            '_': int(time.time()),
        }
        r = self.myRequests.get(url=url, params=params)
        self.tip = 1

        f = open(self.qrcode, 'wb')
        f.write(r.content)
        f.close()

    def get_avatar(self, username):
        path = 'static/img/avatar/' + username[1:] + '.jpg'
        if os.path.exists(path):
            return True
        url = (self.base_uri +
               '/webwxgeticon?username=%s&skey=%s' % (
                   username, self.skey))
        r = self.myRequests.get(url=url)

        f = open(path, 'wb')
        f.write(r.content)
        f.close()
        return True

    def waitForLogin(self):
        url = 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?tip=%s&uuid=%s&_=%s' % (
            self.tip, self.uuid, int(time.time()))

        r = self.myRequests.get(url=url)
        r.encoding = 'utf-8'
        data = r.text

        # print(data)

        # window.code=500;
        regx = r'window.code=(\d+);'
        pm = re.search(regx, data)

        code = pm.group(1)

        if code == '201':  # 已扫描
            print '成功扫描,请在手机上点击确认以登录'
            self.tip = 0
        elif code == '200':  # 已登录
            print '正在登录...'
            regx = r'window.redirect_uri="(\S+?)";'
            pm = re.search(regx, data)
            self.redirect_uri = pm.group(1) + '&fun=new'
            self.base_uri = self.redirect_uri[:self.redirect_uri.rfind('/')]

            # push_uri与base_uri对应关系(排名分先后)(就是这么奇葩..)
            services = [
                ('wx2.qq.com', 'webpush2.weixin.qq.com'),
                ('qq.com', 'webpush.weixin.qq.com'),
                ('web1.wechat.com', 'webpush1.wechat.com'),
                ('web2.wechat.com', 'webpush2.wechat.com'),
                ('wechat.com', 'webpush.wechat.com'),
                ('web1.wechatapp.com', 'webpush1.wechatapp.com'),
            ]
            self.push_uri = self.base_uri
            for (searchUrl, pushUrl) in services:
                if self.base_uri.find(searchUrl) >= 0:
                    self.push_uri = 'https://%s/cgi-bin/mmwebwx-bin' % pushUrl
                    break

            # closeQRImage
            if sys.platform.find('darwin') >= 0:  # for OSX with Preview
                os.system("osascript -e 'quit app \"Preview\"'")
        elif code == '408':  # 超时
            pass
        # elif code == '400' or code == '500':

        return code

    def login(self):
        r = self.myRequests.get(url=self.redirect_uri)
        r.encoding = 'utf-8'
        data = r.text

        # print(data)

        doc = xml.dom.minidom.parseString(data)
        root = doc.documentElement

        for node in root.childNodes:
            if node.nodeName == 'skey':
                self.skey = node.childNodes[0].data
            elif node.nodeName == 'wxsid':
                self.wxsid = node.childNodes[0].data
            elif node.nodeName == 'wxuin':
                self.wxuin = node.childNodes[0].data
            elif node.nodeName == 'pass_ticket':
                self.pass_ticket = node.childNodes[0].data

        # print('skey: %s, wxsid: %s, wxuin: %s, pass_ticket: %s' % (skey, wxsid,
        # wxuin, pass_ticket))

        if not all((self.skey, self.wxsid, self.wxuin, self.pass_ticket)):
            return False

        self.BaseRequest = {
            'Uin': int(self.wxuin),
            'Sid': self.wxsid,
            'Skey': self.skey,
            'DeviceID': self.deviceId,
        }

        return True

    def webwxinit(self):
        url = (self.base_uri +
               '/webwxinit?pass_ticket=%s&skey=%s&r=%s' % (
                   self.pass_ticket, self.skey, int(time.time())))
        params = {'BaseRequest': self.BaseRequest}
        headers = {'content-type': 'application/json; charset=UTF-8'}

        r = self.myRequests.post(url=url, data=json.dumps(params), headers=headers)
        r.encoding = 'utf-8'
        data = r.json()

        # print(data)

        dic = data
        self.ContactList = dic['ContactList']
        self.My = dic['User']
        self.SyncKey = dic['SyncKey']

        state = self.responseState('webwxinit', dic['BaseResponse'])
        return state

    def webwxgetcontact(self):
        url = (self.base_uri +
               '/webwxgetcontact?pass_ticket=%s&skey=%s&r=%s' % (
                   self.pass_ticket, self.skey, int(time.time())))
        headers = {'content-type': 'application/json; charset=UTF-8'}

        r = self.myRequests.post(url=url, headers=headers)
        r.encoding = 'utf-8'
        data = r.json()

        dic = data
        self.MemberList = dic['MemberList']

        # 倒序遍历,不然删除的时候出问题..
        SpecialUsers = ["newsapp", "fmessage", "filehelper", "weibo", "qqmail", "tmessage", "qmessage", "qqsync",
                        "floatbottle", "lbsapp", "shakeapp", "medianote", "qqfriend", "readerapp", "blogapp",
                        "facebookapp",
                        "masssendapp",
                        "meishiapp", "feedsapp", "voip", "blogappweixin", "weixin", "brandsessionholder",
                        "weixinreminder",
                        "wxid_novlwrv3lqwv11", "gh_22b87fa7cb3c", "officialaccounts", "notification_messages", "wxitil",
                        "userexperience_alarm"]
        for i in range(len(self.MemberList) - 1, -1, -1):
            Member = self.MemberList[i]
            if Member['VerifyFlag'] & 8 != 0:  # 公众号/服务号
                self.MemberList.remove(Member)
            elif Member['UserName'] in SpecialUsers:  # 特殊账号
                self.MemberList.remove(Member)
            elif Member['UserName'].find('@@') != -1:  # 群聊
                self.MemberList.remove(Member)
            elif Member['UserName'] == self.My['UserName']:  # 自己
                self.MemberList.remove(Member)
        for member in self.MemberList:
            if member['StarFriend']==0:
                self.unstar_member_count += 1
        self.member_count = len(self.MemberList)
        return self.MemberList

    def webwxsendmsg(self, friend, content):
        clientMsgId = str(int(time.time()))
        url = self.base_uri + "/webwxsendmsg?lang=zh_CN&pass_ticket=" + self.pass_ticket
        Msg = {
            'Type': '1',
            'Content': content,
            'ClientMsgId': clientMsgId.encode('unicode_escape'),
            'FromUserName': self.My['UserName'].encode('unicode_escape'),
            'ToUserName': friend["UserName"].encode('unicode_escape'),
            'LocalID': clientMsgId.encode('unicode_escape')
        }
        payload = {'BaseRequest': self.BaseRequest, 'Msg': Msg}
        headers = {'ContentType': 'application/json; charset=UTF-8'}
        # print str(payload).decode('string_escape')
        data = json.dumps(payload, ensure_ascii=False)
        # r = s.post(url, json=payload, headers=headers)
        r = self.myRequests.post(url, data=data.encode('utf-8'), headers=headers)
        # debugReq(r)
        # print r.text
        resp = json.loads(r.text)
        if 'BaseResponse' in resp:
            if 'Ret' in resp['BaseResponse']:
                return int(resp['BaseResponse']['Ret'])
        return -1

    def syncKey(self):
        SyncKeyItems = ['%s_%s' % (item['Key'], item['Val'])
                        for item in self.SyncKey['List']]
        SyncKeyStr = '|'.join(SyncKeyItems)
        return SyncKeyStr

    def syncCheck(self):
        url = self.push_uri + '/synccheck?'
        params = {
            'skey': self.BaseRequest['Skey'],
            'sid': self.BaseRequest['Sid'],
            'uin': self.BaseRequest['Uin'],
            'deviceId': self.BaseRequest['DeviceID'],
            'synckey': self.syncKey(),
            'r': int(time.time()),
        }

        r = self.myRequests.get(url=url, params=params)
        r.encoding = 'utf-8'
        data = r.text

        # print(data)

        # window.synccheck={retcode:"0",selector:"2"}
        regx = r'window.synccheck={retcode:"(\d+)",selector:"(\d+)"}'
        pm = re.search(regx, data)

        retcode = pm.group(1)
        selector = pm.group(2)

        return selector

    def webwxsync(self):
        url = self.base_uri + '/webwxsync?lang=zh_CN&skey=%s&sid=%s&pass_ticket=%s' % (
            self.BaseRequest['Skey'], self.BaseRequest['Sid'], self.pass_ticket)
        params = {
            'BaseRequest': self.BaseRequest,
            'SyncKey': self.SyncKey,
            'rr': ~int(time.time()),
        }
        headers = {'content-type': 'application/json; charset=UTF-8'}

        r = self.myRequests.post(url=url, data=json.dumps(params))
        r.encoding = 'utf-8'
        data = r.json()

        dic = data
        self.SyncKey = dic['SyncKey']
        state = self.responseState('webwxsync', dic['BaseResponse'])
        for msg in data["AddMsgList"]:
            if msg['MsgType'] == 10000:
                username = msg['FromUserName']
                for member in self.MemberList:
                    if member['UserName'] == username:
                        stranger = model.Stranger(session_id=self.session_id,
                                                  username=member['UserName'],
                                                  nickname=member['NickName'])
                        self.get_avatar(member['UserName'])
                        self.StrangerList.append(member)
                        stranger.save()
                        break
        return state

    def send_to_all(self, msg, except_star):
        client = self.client
        for member in self.MemberList:
            if (not except_star) or member['StarFriend']==0:
                self.webwxsendmsg(member, msg)
                self.webwxsync()
                client.sended_count += 1
                client.save()
                time.sleep(random.randint(1, 3))
        for member in self.StrangerList:
            self.webwxsendmsg(member, msg)
            time.sleep(random.randint(1, 2))
        client.sending = 0
        client.save()

    def send_to_all_friends(self, msg, except_star):
        client = self.client
        client.sending = 1
        client.sended_count = 0
        client.total_count = self.unstar_member_count if except_star else self.member_count
        client.save()
        strangers = list(model.Stranger.select(where="session_id='%s'" % self.session_id))
        model.Stranger.multiple_delete(strangers)
        thread.start_new_thread(self.send_to_all, (msg,except_star))

    @property
    def strangers(self):
        return list(model.Stranger.select(where="session_id='%s'" % self.session_id))

    @property
    def client(self):
        c = model.Client.select(where="session_id='%s'" % self.session_id).first()
        if c is None:
            c = model.Client(session_id=self.session_id, sending=0, sended_count=0, total_count=0)
        return c

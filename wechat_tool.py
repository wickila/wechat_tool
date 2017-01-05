#!/usr/bin/env python
# encoding: utf-8
"""
@author: wicki
@contact: gzswicki@gmail.com
@date: 17/1/1
"""
# -*- encoding: UTF-8 -*-

import json
import web, random
import monkeysql, model
from client import WeChatClient
from jinja2 import Environment, PackageLoader

web.config.debug = True

# url mappings
urls = (
    '/', 'Index',
    '/checklogin', 'CheckLogin',
    '/logout', 'Logout',
    '/progress', 'Progress',
    '/step1', 'Step1',
    '/step2', 'Step2',
    '/step3', 'Step3',
)

app = web.application(urls, globals())
env = Environment(loader=PackageLoader('wechat_tool', 'templates'))

env.filters['dumps'] = json.dumps
env.filters['enumerate'] = enumerate
env.filters['len'] = len


def render(template, **kwargs):
    web.header("Content-Type", "text/html; charset=utf-8")
    client = web.config.session.client
    data = {'user': None if not client else client.My}
    data.update(kwargs)
    output = env.get_template(template).render(data)
    return output.encode('utf-8')


class MyEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, monkeysql.Model):
            return o.to_json()
        elif hasattr(o, '__dict__'):
            d = {}
            for key, value in o.__dict__.items():
                if not key.startswith('_'):
                    d[key] = value
            return d
        return str(o)


def write_json(result, message, **kwargs):
    r = {"result": result, "message": message}
    r.update(kwargs)
    web.header('Content-Type', 'application/json; charset=utf-8')
    return json.dumps(r, cls=MyEncoder, ensure_ascii=False)


def write_txt(text):
    web.header("Content-Type", "text/html; charset=utf-8")
    return text


def need_check_session_api(function):
    def wrap_function(*args):
        session = web.config.session
        result = write_json(False, u"用户未登录", need_login=True)
        if session.user:
            return function(*args, user=session.user)
        return result

    return wrap_function


def get_current_user():
    return web.config.session.user


class Index:
    def GET(self):
        """index page"""
        client = web.config.session.client
        if client is None:
            client = web.config.session.client = WeChatClient(web.config.session.session_id)
        if client.My:
            if client.webwxsync():
                return web.seeother('/step2')
        return render('index.html')


class Step1:
    def GET(self):
        client = web.config.session.client
        if client is None:
            client = web.config.session.client = WeChatClient(web.config.session.session_id)
        if client.My:
            if client.webwxsync():
                return web.seeother('/step2')
        if not client.getUUID():
            return write_json('获取登录二维码失败')
        client.getQRImage()
        return render('step1.html', qrcode=client.qrcode + '?rnd=' + str(random.random()))


class Step2:
    def GET(self):
        client = web.config.session.client
        if client and client.My:
            if not client.webwxsync():
                web.config.session.kill()
                return web.seeother('/step1')
            if client.client.sending:
                return web.seeother('/step3')
            return render('step2.html', me=client.My, sending=client.client.sending, sended=client.client.sended_count)
        return web.seeother('/step1')

    def POST(self):
        data = web.input()
        msg = data.pop('msg', 'please igore this')
        except_star = data.pop('exceptstar', 'false') == 'on'
        client = web.config.session.client
        if client and client.My and not client.client.sending:
            if not client.webwxsync():
                web.config.session.kill()
                return web.seeother('/step1')
            client.send_to_all_friends(msg, except_star)
            return web.seeother('/step3')
        return web.seeother('/step1')


class Step3:
    def GET(self):
        client = web.config.session.client
        if client and client.My:
            strangers = list(model.Stranger.select(where="session_id='%s'" % client.session_id))
            return render('step3.html', strangers=strangers, sending=client.client.sending,
                          sended=client.client.sended_count, total=client.client.total_count)
        return web.seeother('/step1')

class Logout:
    def GET(self):
        web.config.session.kill()
        return web.seeother('/step1')


class CheckLogin():
    def GET(self):
        client = web.config.session.client
        if client:
            if client.My:
                return write_json(True, u'用户已登录')
            else:
                while client.waitForLogin() != '200':
                    pass
                if not client.login():
                    return write_json(False, u'登录失败')
                if not client.webwxinit():
                    return write_json(False, u'初始化失败')
                client.webwxgetcontact()
                return write_json(True, u'用户已登录')
        return write_json(False, u'用户尚未登录')


class Progress:
    def GET(self):
        client = web.config.session.client
        if client and client.My:
            strangers = list(model.Stranger.select(where="session_id='%s'" % client.session_id))
            return write_json(True, u'', strangers=strangers, sending=client.client.sending,
                              sended=client.client.sended_count, total=client.client.total_count)
        return write_json(False, u'用户尚未登录', need_login=True)


if __name__ == '__main__' or __name__.startswith('uwsgi_file'):
    web.config.session_parameters['timeout'] = 3600
    web.config.session = web.session.Session(app, web.session.DiskStore('sessions'),
                                             initializer={'client': None})
    from config import config

    monkeysql.init(dbn='mysql', host=config.database["host"], db=config.database["dbname"],
                   user=config.database["username"],
                   pw=config.database["passwd"])
    if __name__ == '__main__':
        app.run()
    else:
        application = app.wsgifunc()

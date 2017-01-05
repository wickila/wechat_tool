#!/usr/bin/env python
# encoding: utf-8
"""
@author: wicki
@contact: gzswicki@gmail.com
@date: 16/11/7
"""

import monkeysql
import datetime
import random


class Client(monkeysql.Model):
    __tablename__ = 'client'

    def __init__(self, **kwargs):
        monkeysql.Model.__init__(self, **kwargs)
        self.session_id = kwargs.pop('session_id')
        self.sending = kwargs.pop('sending')
        self.sended_count = kwargs.pop('sended_count')
        self.total_count = kwargs.pop('total_count')


class Stranger(monkeysql.Model):
    __tablename__ = 'stranger'

    def __init__(self, **kwargs):
        monkeysql.Model.__init__(self, **kwargs)
        self.session_id = kwargs.pop('session_id')
        self.username = kwargs.pop('username')
        self.nickname = kwargs.pop('nickname')

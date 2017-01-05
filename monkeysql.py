# -*- encoding: UTF-8 -*-
"""
Created on 2015年7月9日
数据库ORM封装
@author: wicki
"""
import web
import json

db = None


def init(dburl=None, **params):
    global db
    db = web.database(dburl, **params)


class Model(object):
    """数据模型基类，默认主键为id"""
    __tablename__ = ""

    def __init__(self, **kwargs):
        if not db:
            raise Exception("please init database first!!!")
        self._dirty = []
        if "id" in kwargs:
            self.id = kwargs.pop("id")

    def __setattr__(self, *args, **kwargs):
        key = args[0]
        value = args[1]
        if key in self.__dict__ and getattr(self, key) != value:
            self._dirty.append(key)
        return object.__setattr__(self, *args, **kwargs)

    def getinsertrow(self):
        params = [param for param in self.__dict__ if ((not callable(param)) and param.find("_") != 0)]
        keyvalues = {}
        for param in params:
            keyvalues[param] = getattr(self, param)
        return keyvalues

    def _getupdaterow(self):
        keyvalues = {}
        for key in self._dirty:
            keyvalues[key] = getattr(self, key)
        return keyvalues

    def save(self):
        """如果该数据对象是新建的或者有改变，则写入数据库，如果没改变，则不作任何操作"""
        if not "id" in self.__dict__:
            self.id = db.insert(self.__tablename__, **self.getinsertrow())
        elif len(self._dirty) > 0:
            db.update(self.__tablename__, where=('id=%d' % self.id), **self._getupdaterow())
            self._dirty = []

    def delete(self):
        """立即从数据库中删除对象"""
        if self.id is not None:
            db.delete(self.__tablename__, where=('id=%d' % self.id))

    def to_json(self):
        params = [param for param in dir(self) if ((not callable(getattr(self, param))) and param.find("_") != 0)]
        keyvalues = {}
        for param in params:
            keyvalues[param] = getattr(self, param)
        return keyvalues

    @classmethod
    def select(cls, **kwargs):
        """
            从数据库中查询数据，并且封装成数据对象返回
                ex:users = monkeysql.select(User,where="id=1")
                详细用法参见web.py数据库的select用法:http://webpy.org/cookbook/select.zh-cn
        """
        result = []
        dbn = cls.__tablename__ if 'dbn' not in kwargs else kwargs.pop('dbn')
        query = db.select(dbn, **kwargs)
        for dbobj in query:
            result.append(cls(**dict(dbobj)))
        return web.utils.iterbetter(iter(result))

    @classmethod
    def get_by_id(cls, id, **kwargs):
        return cls.select(where='id=%d' % int(id), **kwargs).first()

    @classmethod
    def all(cls):
        return cls.select()

    @classmethod
    def count(cls, **kwargs):
        return db.select(cls.__tablename__, what='count(id) as count', **kwargs).first().count

    @classmethod
    def multiple_insert(cls, values):
        """
            批量插入数据
            ex:
            users = [User(username="test1"),User(username="test2")]
            out = monkeysql.multiple_insert(User,users)
            print users[1].id
        """
        out = db.multiple_insert(cls.__tablename__, [value.getinsertrow() for value in values])
        for index, value in enumerate(values):
            value.id = out[index] + len(values) - 1  # 因为mysql在批量插入后,返回的最新ID是批量插入的第一个,所以这里要修正

    @classmethod
    def multiple_delete(cls, values):
        """
            批量删除数据
            ex:
            monkeysql.multiple_delete(User,users)
        """
        if len(values) > 0:
            db.delete(cls.__tablename__, where="id in (%s)" % ",".join([str(value.id) for value in values]))

    @classmethod
    def multiple_update(cls, instants, **values):
        """
            批量更新数据
            ex:
            monkeysql.multiple_update(User,users, name='foo')
        """
        if len(instants) > 0:
            db.update(cls.__tablename__, where="id in (%s)" % ",".join([str(value.id) for value in instants]), **values)


class ResultProxy:
    def __init__(self):
        pass

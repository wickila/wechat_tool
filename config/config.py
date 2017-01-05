#!/usr/bin/env python
# encoding: utf-8
"""
@author: wicki
@contact: gzswicki@gmail.com
@date: 16/7/12
"""

import json
import os

if os.path.exists('./config/config.json'):
    with open("./config/config.json") as f:
        config = json.load(f)
        globals().update(config)


if __name__ == "__main__":
    """ general config.json """

    config_template = {"database": {
        "host": "you mysql host",
        "dbname": "your dbname",
        "username": "username",
        "passwd": "password"
    }}
    with open('./config.json', 'w') as f:
        json.dump(config_template, f)

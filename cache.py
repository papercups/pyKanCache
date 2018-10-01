#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
from contextlib import closing


CACHE_PATH = os.path.join(os.getcwd(), 'cache')
CHECK_JSON_PATH = os.path.join(CACHE_PATH, 'check.json')

# 初始化缓存文件夹和校验用json
if not os.path.isdir(CACHE_PATH):
    os.mkdir(CACHE_PATH)

if os.path.isfile(CHECK_JSON_PATH):
    with open(CHECK_JSON_PATH, 'r') as fp:
        check_json = json.load(fp)
else:
    with open(CHECK_JSON_PATH, 'w') as fp:
        fp.write('{}')
    check_json = dict()


# 检测缓存有效性
def checkCache(cache_path, version):
    '''
    args:
        cache_path: 缓存文件相对路径
        version: 缓存版本号,没有时为None

    return:
        0: 可以使用
        1: 无效或不存在,要下载
        文件修改时间: 过期,需要向服务器验证
    '''

    if cache_path not in check_json:
        return 1

    file_path = os.path.join(CACHE_PATH, cache_path)
    # 检查文件是否存在
    if not os.path.isfile(file_path):
        return 1

    # 带version的先检查version
    if version:
        # 不一致的的话就要重新下载
        if version != check_json[cache_path]['version']:
            return 1

    # 检查是否过期
    deadline = float(check_json[cache_path]['deadline'])
    # 过期要用If-Modified-Since检测
    if deadline < time.time():
        # 返回修改时间,肯定大于1
        return os.path.getmtime(file_path)

    # 三个检查都通过的可以使用
    return 0


def getCache(cache_path):
    file_name = os.path.join(CACHE_PATH, cache_path)
    cache_byte = b''
    with closing(
        open(file_name, 'rb')
    ) as fp:
        cache_byte = fp.read()
        return cache_byte

def setCache(cache_byte, cache_path, cache_json):
    file_path, file_name = os.path.split(cache_path)
    file_path = os.path.join(CACHE_PATH, file_path)
    file_name = os.path.join(file_path, file_name)
    if not os.path.isdir(file_path):
        try:
            os.makedirs(file_path)
        except:
            pass

    with closing(
        open(file_name, 'wb')
    ) as fp:
        fp.write(cache_byte)

    check_json.update({cache_path:cache_json})
    with closing(
        open(CHECK_JSON_PATH, 'w')
    ) as fp:
        json.dump(check_json.copy(), fp)

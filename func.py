#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time

# 服务器时间字符串转time时间戳
def modified2Stamp(last_modified):
    return time.mktime(
        time.strptime(
            last_modified,
            '%a, %d %b %Y %H:%M:%S GMT'
        )
    )

# time时间戳转服务器时间字符串
def stamp2Modified(last_modified_time):
    return time.strftime(
        '%a, %d %b %Y %H:%M:%S GMT',
        time.gmtime(last_modified_time)
    )

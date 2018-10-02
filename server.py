#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from contextlib import closing
import os
import time

from flask import Flask, request, Response
import requests

import cache
import func


# 缓存文件响应头
cache_headers = {
    'Server': 'nginx',
    'Pragma': 'no-cache',
    #'Cache-Control': 'no-cache',
    'Accept-Ranges': 'byte',
}
# 不同类型文件的Content-Type
Content_Types = {
    '.png': {'Content-Type': 'image/png'},
    '.mp3': {'Content-Type': 'audio/mpeg'},
    '.json': {'Content-Type': 'application/json'},
    '.css': {'Content-Type': 'text/css'},
}

app = Flask('pyKanCache')
# 上游代理
proxies = {
    'http': 'http://127.0.0.1:8888'
}

# 代理GET请求
@app.route('/<path:subpath>', methods = ['GET'])
def proxyGET(subpath):
    # 用扩展名判断是否使用本地缓存
    cache_type = os.path.splitext(subpath)[1]
    if cache_type in ('.png', '.mp3', '.json'):
        # 先检测缓存是否有效
        cache_flag = cache.checkCacheServer(
            subpath,
            request.args.get('version', default = None)
        )

        if cache_flag > 0:
            # 带着cache_flag进download,需要验证时就带If-Modified-Since
            resp = download(request, cache_flag)
            cache_byte = resp.data
        # 缓存有效或验证后返回304时用本地缓存
        if cache_flag == 0 or resp.status_code == 304:
            # 浏览器发送If-Modified-Since且是符合缓存内容时,要先检测这个
            if 'If-Modified-Since' in request.headers:
                last_modified = request.headers.get('If-Modified-Since')
                if cache.checkCacheBrowser(subpath, last_modified):
                    return Response('', 304, cache_headers)

            app.logger.debug('使用本地缓存: %s', subpath)
            cache_byte, last_modified = cache.getCache(subpath)
        else:
            last_modified = resp.headers['Last-Modified']
            cache_json = {
                'deadline': str(time.time() + 2592000),
                'version': request.args.get('version', default = None),
                'last_modified': last_modified,
            }
            cache.setCache(cache_byte, subpath, cache_json)
        # 用扩展名完成headers
        cache_headers.update(Content_Types[cache_type])
        cache_headers['Content-Length'] = len(cache_byte)
        cache_headers['Last-Modified'] = last_modified
        return Response(cache_byte, 200, cache_headers)

    else:
        app.logger.debug('转发GET: %s', request.url)
        return transmitGET(request)

@app.route('/<path:subpath>', methods = ['POST'])
def proxyPOST(subpath):
    resp = transmitPOST(request)
    if resp.status_code == 201:
        app.logger.warning('错误代码: 201')
    return resp

def transmitPOST(request):
    '''直接转发POST请求
    '''

    url = request.url
    data = request.form or None
    headers = dict(request.headers)

    with closing(
        requests.post(
            url, headers = headers, data = data, proxies=proxies)
    ) as r:
        headers = dict(r.headers)
        if headers.get('Content-Encoding') and \
           headers['Content-Encoding'] in ('gzip', 'deflate'):
            del headers['Content-Encoding']
        if headers.get('Transfer-Encoding'):
            del headers['Transfer-Encoding']
        headers['Content-Length'] = len(r.content)

        return Response(r.content, r.status_code, headers)

def transmitGET(request):
    '''直接转发GET请求
    '''

    url = request.url
    data = request.data or None
    '''好像不用特地去掉Cache-Control?
    headers = dict()
    for key, value in request.headers:
        if not value or key == 'Cache-Control':
            continue
        headers[key] = value
    '''
    headers = dict(request.headers)

    with closing(
        requests.get(
            url, headers = headers, data = data, stream = True)
    ) as r:
        headers = dict(r.headers)
        if headers.get('Content-Encoding') and \
           headers['Content-Encoding'] in ('gzip', 'deflate'):
            del headers['Content-Encoding']
        if headers.get('Transfer-Encoding'):
            del headers['Transfer-Encoding']
        headers['Content-Length'] = len(r.content)

        return Response(r.content, r.status_code, headers)

# 下载缓存文件
def download(request, cache_flag):
    url = request.url
    data = request.data or None
    headers = dict()
    for key, value in request.headers:
        if not value or key == 'Cache-Control':
            continue
        headers[key] = value
    if cache_flag > 1:
        app.logger.debug('验证缓存有效性: %s', request.path)
        headers['If-Modified-Since'] = cache.getCacheModified(cache_flag)
    else:
        app.logger.debug('下载缓存: %s', request.url)

    with closing(
        requests.get(
            url, headers = headers, data = data, stream = True)
    ) as r:
        headers = dict(r.headers)
        return Response(r.content, r.status_code, headers)

app.run(port = 8007, debug = True)

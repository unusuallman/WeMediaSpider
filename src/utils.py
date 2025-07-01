#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
微信公众号爬虫 - 工具函数模块
==========================

提供爬虫过程中需要的各种实用工具函数，包括公众号搜索、
文章URL获取、内容解析等功能，这些函数被其他模块调用。

主要功能:
    1. 公众号搜索 - 根据名称获取公众号fakeid
    2. 文章列表获取 - 分页获取公众号文章列表
    3. 时间戳转换 - 将时间戳转换为可读格式
    4. 关键词筛选 - 根据关键词筛选文章标题

版本: 1.0
"""

import requests
import random
import time
import os
import csv
from datetime import datetime
from tqdm import tqdm
import bs4


def get_fakid(headers, tok, query):
    """
    获取公众号fakeid
    
    Args:
        headers: 请求头，包含cookie等认证信息
        tok: 访问token
        query: 公众号名称关键词
        
    Returns:
        list: 包含匹配公众号信息的字典列表，每个字典包含wpub_name和wpub_fakid
    """
    url = 'https://mp.weixin.qq.com/cgi-bin/searchbiz'
    data = {
        'action': 'search_biz',
        'scene': 1,
        'begin': 0,
        'count': 10,
        'query': query,
        'token': tok,
        'lang': 'zh_CN',
        'f': 'json',
        'ajax': '1',
    }
    
    # 发送请求
    r = requests.get(url, headers=headers, params=data)
    
    # 解析json
    dic = r.json()
    
    # 获取公众号名称、fakeid
    wpub_list = [
        {
            'wpub_name': item['nickname'],
            'wpub_fakid': item['fakeid']
        }
        for item in dic['list']
    ]
    
    return wpub_list


def get_articles_list(page_num, start_page, fakeid, token, headers):
    """
    获取公众号文章列表
    
    Args:
        page_num: 要获取的页数
        start_page: 起始页码
        fakeid: 公众号的fakeid
        token: 访问token
        headers: 请求头
        
    Returns:
        tuple: (标题列表, 链接列表, 时间戳列表)
    """
    url = 'https://mp.weixin.qq.com/cgi-bin/appmsg'
    title = []
    link = []
    update_time = []
    
    with tqdm(total=page_num) as pbar:
        for i in range(page_num):
            data = {
                'action': 'list_ex',
                'begin': start_page + i*5,       #页数
                'count': '5',
                'fakeid': fakeid,
                'type': '9',
                'query':'',
                'token': token,
                'lang': 'zh_CN',
                'f': 'json',
                'ajax': '1',
            }
            
            # 随机延时，避免被反爬
            time.sleep(random.randint(1, 2))
            
            r = requests.get(url, headers=headers, params=data)
            # 解析json
            dic = r.json()
            
            # 检查是否有文章列表
            if 'app_msg_list' not in dic:
                print(f"警告: 未找到文章列表, 响应为: {dic}")
                break
                
            for item in dic['app_msg_list']:
                title.append(item['title'])      # 获取标题
                link.append(item['link'])        # 获取链接
                update_time.append(item['update_time'])  # 获取更新时间戳
                
            pbar.update(1)
    
    return title, link, update_time


def get_article_content(url, headers):
    """
    获取单篇文章的内容
    
    Args:
        url: 文章链接
        headers: 请求头
        
    Returns:
        str: 文章内容
    """
    try:
        # 发送请求
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return f"请求失败，状态码: {response.status_code}"
        
        # 解析HTML
        soup = bs4.BeautifulSoup(response.text, 'html.parser')
        
        # 查找正文段落
        soup_sel = soup.select("p")
        content = ""
        for c in soup_sel:
            t = c.get_text().strip('\n')
            if t != '':
                content += t + "\n"
                
        # 提取有效内容部分，避免页面头尾部分
        if len(content) > 150:
            content = content[116:-11]
            
        return content
        
    except Exception as e:
        return f"获取文章内容失败: {str(e)}"


def get_timestamp(update_time):
    """
    将时间戳转换为可读时间
    
    Args:
        update_time: UNIX时间戳
        
    Returns:
        str: 格式化的时间字符串 (YYYY-MM-DD HH:MM:SS)
    """
    try:
        dt = datetime.fromtimestamp(int(update_time))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        return f"时间戳转换失败: {str(e)}"


def format_time(timestamp):
    """
    格式化时间戳
    
    Args:
        timestamp: UNIX时间戳
        
    Returns:
        str: 格式化的日期时间 (YYYY-MM-DD HH:MM:SS)
    """
    try:
        dt = datetime.fromtimestamp(int(timestamp))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return ''


def filter_by_keywords(articles, keywords, field='title'):
    """
    根据关键词过滤文章
    
    Args:
        articles: 文章列表，每篇文章为一个字典
        keywords: 关键词列表
        field: 要搜索的字段，默认为'title'
        
    Returns:
        list: 匹配关键词的文章列表
    """
    if not keywords:
        return articles
    
    filtered = []
    for article in articles:
        if field not in article:
            continue
            
        content = article[field].lower()
        if any(keyword.lower() in content for keyword in keywords):
            filtered.append(article)
            
    return filtered


def save_to_csv(data, filename, fieldnames=None):
    """
    将数据保存为CSV文件
    
    Args:
        data: 要保存的数据列表
        filename: 文件名
        fieldnames: 字段名列表，默认为None（自动获取）
        
    Returns:
        bool: 保存是否成功
    """
    try:
        # 确保目录存在
        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        # 如果fieldnames未提供，尝试从第一个数据项获取
        if not fieldnames and data:
            if isinstance(data[0], dict):
                fieldnames = list(data[0].keys())
        
        # 必须有字段名
        if not fieldnames:
            print(f"保存CSV失败: 未提供字段名且无法自动获取")
            return False
        
        # 写入CSV
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
            
        print(f"数据已保存到: {filename}")
        return True
        
    except Exception as e:
        print(f"保存CSV失败: {str(e)}")
        return False


def mkdir(path):
    """
    创建目录
    
    Args:
        path: 目录路径
        
    Returns:
        bool: 创建是否成功
    """
    # 去除首尾空格和反斜杠
    path = path.strip().rstrip("\\")
    
    # 判断路径是否存在
    if not os.path.exists(path):
        # 创建目录
        os.makedirs(path)
        print(f"{path} 创建成功")
        return True
    else:
        print(f"{path} 目录已存在")
        return False 
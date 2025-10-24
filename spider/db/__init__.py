#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
内容爬虫 - 数据库模块
=================

提供数据库管理功能, 存储爬取的账号和文章信息并支持查询操作。
使用SQLAlchemy ORM, 支持多种数据库后端, 默认使用SQLite。

主要功能:
    1. 数据库初始化 - 创建数据库结构
    2. 账号管理 - 存储和查询不同平台的账号
    3. 文章存储 - 将爬取的文章存储到数据库
    4. 查询功能 - 支持多种条件的文章查询

版本: 3.0 (ORM重构)
"""

from .interface import DatabaseORM
from .models import Account, Article
from .factory import DatabaseFactory

__all__ = [
    'DatabaseORM',
    'Account',
    'Article',
    'DatabaseFactory'
]
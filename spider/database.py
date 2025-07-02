#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
微信公众号爬虫 - 数据库模块
========================

提供数据库管理功能，存储爬取的文章信息并支持查询操作。
采用SQLite作为数据库后端，提供简单高效的存储方案。

主要功能:
    1. 数据库初始化 - 创建数据库结构
    2. 文章存储 - 将爬取的文章存储到数据库
    3. 批次管理 - 追踪不同批次的爬取任务
    4. 查询功能 - 支持多种条件的文章查询

版本: 1.0
"""

import os
import json
import time
import sqlite3
from datetime import datetime
import threading


class ArticleDatabase:
    """文章数据库管理器"""
    
    def __init__(self, db_file='wechat_articles.db'):
        """
        初始化数据库管理器
        
        Args:
            db_file: 数据库文件路径
        """
        self.db_file = db_file
        self.lock = threading.Lock()
        self.init_database()
    
    def init_database(self):
        """初始化数据库表结构"""
        with self.lock:
            # 确保数据库文件所在目录存在
            os.makedirs(os.path.dirname(os.path.abspath(self.db_file)), exist_ok=True)
            
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # 创建文章表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_name TEXT NOT NULL,
                    title TEXT NOT NULL,
                    link TEXT UNIQUE NOT NULL,
                    digest TEXT,
                    publish_time TEXT,
                    publish_timestamp INTEGER,
                    content TEXT,
                    batch_id TEXT,
                    created_at INTEGER DEFAULT (strftime('%s', 'now')),
                    UNIQUE(link)
                )
            ''')
            
            # 创建批次表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS batch_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id TEXT UNIQUE NOT NULL,
                    start_date TEXT,
                    end_date TEXT,
                    accounts TEXT,
                    total_articles INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'running',
                    created_at INTEGER DEFAULT (strftime('%s', 'now')),
                    completed_at INTEGER
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_account_time ON articles(account_name, publish_timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_batch_id ON articles(batch_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_time_range ON articles(publish_timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_account_name ON articles(account_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_created_at ON articles(created_at)')
            
            conn.commit()
            conn.close()
            
            print(f"数据库初始化完成: {self.db_file}")
    
    def create_batch(self, batch_id, start_date, end_date, accounts):
        """
        创建新的批次记录
        
        Args:
            batch_id: 批次ID
            start_date: 开始日期
            end_date: 结束日期
            accounts: 账号列表
            
        Returns:
            str: 批次ID
        """
        with self.lock:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO batch_info 
                (batch_id, start_date, end_date, accounts, status)
                VALUES (?, ?, ?, ?, 'running')
            ''', (batch_id, start_date, end_date, json.dumps(accounts)))
            
            conn.commit()
            conn.close()
            
            print(f"创建批次: {batch_id}, 包含 {len(accounts)} 个公众号")
            return batch_id
    
    def save_article(self, article, batch_id=None):
        """
        保存文章到数据库
        
        Args:
            article: 文章信息字典
            batch_id: 批次ID
            
        Returns:
            bool: 保存是否成功
        """
        with self.lock:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            try:
                # 检查文章是否已存在
                cursor.execute("SELECT id FROM articles WHERE link=?", (article['link'],))
                existing = cursor.fetchone()
                
                if existing:
                    # 如果文章已存在，更新部分字段
                    cursor.execute('''
                        UPDATE articles SET 
                        digest=?, content=?, batch_id=?
                        WHERE link=?
                    ''', (
                        article.get('digest', ''),
                        article.get('content', ''),
                        batch_id,
                        article['link']
                    ))
                else:
                    # 插入新文章
                    cursor.execute('''
                        INSERT INTO articles 
                        (account_name, title, link, digest, content, publish_time, 
                         publish_timestamp, batch_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        article['name'],
                        article['title'],
                        article['link'],
                        article.get('digest', ''),
                        article.get('content', ''),
                        article.get('publish_time', ''),
                        article.get('publish_timestamp', 0),
                        batch_id
                    ))
                
                conn.commit()
                conn.close()
                return True
                
            except Exception as e:
                print(f"保存文章到数据库失败: {e}")
                conn.rollback()
                conn.close()
                return False
    
    def complete_batch(self, batch_id, total_articles=None):
        """
        完成批次任务
        
        Args:
            batch_id: 批次ID
            total_articles: 文章总数，如果为None则自动计算
            
        Returns:
            int: 批次中的文章总数
        """
        with self.lock:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # 如果未提供文章总数，则自动计算
            if total_articles is None:
                cursor.execute("SELECT COUNT(*) FROM articles WHERE batch_id=?", (batch_id,))
                total_articles = cursor.fetchone()[0]
            
            # 更新批次信息
            cursor.execute('''
                UPDATE batch_info 
                SET status='completed', completed_at=strftime('%s', 'now'), total_articles=?
                WHERE batch_id=?
            ''', (total_articles, batch_id))
            
            conn.commit()
            conn.close()
            
            print(f"批次 {batch_id} 已完成，共 {total_articles} 篇文章")
            return total_articles
    
    def get_articles(self, batch_id=None, account_name=None, start_date=None, end_date=None, 
                   keywords=None, limit=100, offset=0):
        """
        查询文章
        
        Args:
            batch_id: 批次ID
            account_name: 公众号名称
            start_date: 开始日期，格式为YYYY-MM-DD
            end_date: 结束日期，格式为YYYY-MM-DD
            keywords: 关键词列表，在标题或内容中搜索
            limit: 返回条数限制
            offset: 查询偏移量
            
        Returns:
            list: 文章列表
        """
        with self.lock:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row  # 返回字典格式的结果
            cursor = conn.cursor()
            
            query = "SELECT * FROM articles WHERE 1=1"
            params = []
            
            # 添加过滤条件
            if batch_id:
                query += " AND batch_id=?"
                params.append(batch_id)
                
            if account_name:
                query += " AND account_name LIKE ?"
                params.append(f'%{account_name}%')
                
            if start_date:
                # 转换日期为时间戳
                start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
                query += " AND publish_timestamp >= ?"
                params.append(start_ts)
                
            if end_date:
                # 转换日期为时间戳，加上一天的秒数-1，以包含整天
                end_ts = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp()) + 86399
                query += " AND publish_timestamp <= ?"
                params.append(end_ts)
                
            if keywords:
                # 构建关键词搜索条件
                keyword_conditions = []
                for keyword in keywords:
                    keyword_conditions.append("title LIKE ? OR content LIKE ?")
                    params.extend([f'%{keyword}%', f'%{keyword}%'])
                    
                if keyword_conditions:
                    query += " AND (" + " OR ".join(keyword_conditions) + ")"
            
            # 添加排序、分页
            query += " ORDER BY publish_timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            # 执行查询
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # 转换结果为字典列表
            articles = []
            for row in results:
                article = dict(row)
                articles.append(article)
                
            conn.close()
            return articles
    
    def get_batch_info(self, batch_id=None):
        """
        获取批次信息
        
        Args:
            batch_id: 批次ID，如果为None则获取全部批次
            
        Returns:
            list: 批次信息列表
        """
        with self.lock:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if batch_id:
                cursor.execute("SELECT * FROM batch_info WHERE batch_id=?", (batch_id,))
                result = cursor.fetchone()
                info = dict(result) if result else None
                
                # 解析账号列表
                if info and 'accounts' in info:
                    try:
                        info['accounts'] = json.loads(info['accounts'])
                    except:
                        info['accounts'] = []
                        
                conn.close()
                return info
            else:
                cursor.execute("SELECT * FROM batch_info ORDER BY created_at DESC")
                results = cursor.fetchall()
                
                batch_list = []
                for row in results:
                    info = dict(row)
                    # 解析账号列表
                    if 'accounts' in info:
                        try:
                            info['accounts'] = json.loads(info['accounts'])
                        except:
                            info['accounts'] = []
                            
                    batch_list.append(info)
                    
                conn.close()
                return batch_list
    
    def count_articles(self, batch_id=None, account_name=None):
        """
        计算文章数量
        
        Args:
            batch_id: 批次ID
            account_name: 公众号名称
            
        Returns:
            int: 文章数量
        """
        with self.lock:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            query = "SELECT COUNT(*) FROM articles WHERE 1=1"
            params = []
            
            if batch_id:
                query += " AND batch_id=?"
                params.append(batch_id)
                
            if account_name:
                query += " AND account_name LIKE ?"
                params.append(f'%{account_name}%')
                
            cursor.execute(query, params)
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
    
    def get_unique_accounts(self):
        """
        获取数据库中的所有唯一公众号名称
        
        Returns:
            list: 公众号名称列表
        """
        with self.lock:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute("SELECT DISTINCT account_name FROM articles ORDER BY account_name")
            accounts = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return accounts 
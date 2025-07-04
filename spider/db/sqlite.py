#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SQLite数据库实现
===============

使用SQLite作为后端的数据库实现。
"""

import os
import json
import time
import sqlite3
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional

from spider.db.interface import DatabaseInterface
from spider.log.utils import logger

class SQLiteDatabase(DatabaseInterface):
    """SQLite数据库实现"""
    
    def __init__(self, db_file='content_spider.db'):
        """
        初始化SQLite数据库
        
        Args:
            db_file: 数据库文件路径
        """
        self.db_file = db_file
        self.lock = threading.Lock()
        self.init_database()
    
    def init_database(self) -> None:
        """初始化数据库表结构"""
        with self.lock:
            # 确保数据库文件所在目录存在
            os.makedirs(os.path.dirname(os.path.abspath(self.db_file)), exist_ok=True)
            
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # 创建账号表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    account_id TEXT,
                    details TEXT,
                    created_at INTEGER DEFAULT (strftime('%s', 'now')),
                    updated_at INTEGER DEFAULT (strftime('%s', 'now')),
                    UNIQUE(platform, account_id),
                    UNIQUE(platform, name)
                )
            ''')
            
            # 创建文章表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    publish_time TEXT,
                    publish_timestamp INTEGER,
                    content TEXT,
                    details TEXT,
                    created_at INTEGER DEFAULT (strftime('%s', 'now')),
                    updated_at INTEGER DEFAULT (strftime('%s', 'now')),
                    FOREIGN KEY (account_id) REFERENCES accounts(id),
                    UNIQUE(url)
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_account ON articles(account_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_timestamp ON articles(publish_timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_accounts_platform ON accounts(platform)')
            
            conn.commit()
            conn.close()
            
            logger.info(f"数据库初始化完成: {self.db_file}")
    
    def save_account(self, name: str, platform: str, account_id: Optional[str] = None, 
                    details: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """保存账号信息"""
        with self.lock:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            details_json = json.dumps(details or {}, ensure_ascii=False)
            timestamp = int(time.time())
            
            try:
                # 检查账号是否已存在
                if account_id:
                    cursor.execute(
                        "SELECT id FROM accounts WHERE platform=? AND account_id=?", 
                        (platform, account_id)
                    )
                else:
                    cursor.execute(
                        "SELECT id FROM accounts WHERE platform=? AND name=?", 
                        (platform, name)
                    )
                existing = cursor.fetchone()
                
                if existing:
                    logger.info(f"更新已有账号: {name}, {platform}, {account_id}")
                    # 更新已有账号
                    account_db_id = existing[0]
                    cursor.execute('''
                        UPDATE accounts SET 
                        name=?, account_id=?, details=?, updated_at=?
                        WHERE id=?
                    ''', (name, account_id or "", details_json, timestamp, account_db_id))
                else:
                    logger.info(f"插入新账号: {name}, {platform}, {account_id}")
                    # 插入新账号
                    try:
                        cursor.execute('''
                            INSERT INTO accounts 
                            (name, platform, account_id, details, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (name, platform, account_id or "", details_json, timestamp, timestamp))
                        account_db_id = cursor.lastrowid
                    except sqlite3.IntegrityError as e:
                        if "UNIQUE constraint failed" in str(e):
                            # 发生唯一约束冲突，尝试获取已存在记录的ID
                            logger.warning(f"账号已存在 ({name}, {platform}, {account_id}), 尝试获取已有ID")
                            
                            # 再次查询可能是多个条件组合导致的冲突
                            cursor.execute(
                                "SELECT id FROM accounts WHERE (platform=? AND account_id=?) OR (platform=? AND name=?)", 
                                (platform, account_id or "", platform, name)
                            )
                            existing = cursor.fetchone()
                            if existing:
                                account_db_id = existing[0]
                            else:
                                # 如果还是找不到，抛出原始异常
                                raise
                        else:
                            # 其他完整性错误，重新抛出
                            raise
                
                conn.commit()
                conn.close()
                
                return str(account_db_id)
                
            except Exception as e:
                logger.error(f"保存账号失败: {e}")
                conn.rollback()
                conn.close()
                return None
    
    def get_account(self, id: Optional[str] = None, name: Optional[str] = None, 
                   platform: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取账号信息"""
        with self.lock:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if id:
                cursor.execute("SELECT * FROM accounts WHERE id=?", (id,))
            elif name and platform:
                cursor.execute("SELECT * FROM accounts WHERE name=? AND platform=?", (name, platform))
            else:
                conn.close()
                return None
                
            row = cursor.fetchone()
            if not row:
                conn.close()
                return None
                
            account = dict(row)
            # 解析details字段
            if 'details' in account and account['details']:
                try:
                    account['details'] = json.loads(account['details'])
                except:
                    account['details'] = {}
            
            conn.close()
            return account
    
    def save_article(self, account_id: str, title: str, url: str, 
                    publish_time: Optional[str] = None, content: Optional[str] = None, 
                    details: Optional[Dict[str, Any]] = None) -> bool:
        """保存文章"""
        with self.lock:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            details_json = json.dumps(details or {}, ensure_ascii=False)
            timestamp = int(time.time())
            
            # 计算发布时间的时间戳
            publish_timestamp = 0
            if publish_time:
                try:
                    dt = datetime.strptime(publish_time, "%Y-%m-%d %H:%M:%S")
                    publish_timestamp = int(dt.timestamp())
                except:
                    # 如果转换失败，使用当前时间
                    publish_timestamp = timestamp
            
            try:
                # 检查文章是否已存在
                cursor.execute("SELECT id FROM articles WHERE url=?", (url,))
                existing = cursor.fetchone()
                
                if existing:
                    # 更新已有文章
                    article_id = existing[0]
                    cursor.execute('''
                        UPDATE articles SET 
                        account_id=?, title=?, content=?, details=?, updated_at=?
                        WHERE id=?
                    ''', (
                        account_id, title, content or "", details_json, timestamp, article_id
                    ))
                else:
                    # 插入新文章
                    cursor.execute('''
                        INSERT INTO articles 
                        (account_id, title, url, publish_time, publish_timestamp, content, details, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        account_id, title, url, publish_time or "", publish_timestamp,
                        content or "", details_json, timestamp, timestamp
                    ))
                
                conn.commit()
                conn.close()
                return True
                
            except Exception as e:
                logger.error(f"保存文章失败: {e}")
                conn.rollback()
                conn.close()
                return False
    
    def get_articles(self, account_id: Optional[str] = None, platform: Optional[str] = None,
                   start_date: Optional[str] = None, end_date: Optional[str] = None, 
                   keywords: Optional[List[str]] = None, limit: int = 100, 
                   offset: int = 0) -> List[Dict[str, Any]]:
        """查询文章"""
        with self.lock:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if platform and not account_id:
                # 如果只提供了平台，需要先查询该平台的所有账号
                base_query = """
                    SELECT a.* FROM articles a
                    JOIN accounts acc ON a.account_id = acc.id
                    WHERE acc.platform = ?
                """
                params = [platform]
            else:
                base_query = "SELECT * FROM articles WHERE 1=1"
                params = []
                
                if account_id:
                    base_query += " AND account_id=?"
                    params.append(account_id)
            
            # 添加日期过滤
            if start_date:
                start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
                base_query += " AND publish_timestamp >= ?"
                params.append(str(start_ts))
                
            if end_date:
                # 加上一天的秒数-1，以包含整天
                end_ts = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp()) + 86399
                base_query += " AND publish_timestamp <= ?"
                params.append(str(end_ts))
            
            # 关键词搜索
            if keywords:
                keyword_conditions = []
                for keyword in keywords:
                    keyword_conditions.append("(title LIKE ? OR content LIKE ?)")
                    params.extend([f'%{keyword}%', f'%{keyword}%'])
                    
                if keyword_conditions:
                    base_query += " AND (" + " OR ".join(keyword_conditions) + ")"
            
            # 排序和分页
            query = base_query + " ORDER BY publish_timestamp DESC LIMIT ? OFFSET ?"
            params.extend([str(limit), str(offset)])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            articles = []
            for row in rows:
                article = dict(row)
                # 解析details字段
                if 'details' in article and article['details']:
                    try:
                        article['details'] = json.loads(article['details'])
                    except:
                        article['details'] = {}
                articles.append(article)
            
            conn.close()
            return articles
    
    def count_articles(self, account_id: Optional[str] = None, platform: Optional[str] = None) -> int:
        """统计文章数量"""
        with self.lock:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            if platform and not account_id:
                # 如果只提供了平台，需要统计该平台所有账号的文章
                query = """
                    SELECT COUNT(*) FROM articles a
                    JOIN accounts acc ON a.account_id = acc.id
                    WHERE acc.platform = ?
                """
                cursor.execute(query, (platform,))
            elif account_id:
                query = "SELECT COUNT(*) FROM articles WHERE account_id=?"
                cursor.execute(query, (account_id,))
            else:
                cursor.execute("SELECT COUNT(*) FROM articles")
                
            count = cursor.fetchone()[0]
            conn.close()
            return count
    
    def get_platforms(self) -> List[str]:
        """获取所有平台类型"""
        with self.lock:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute("SELECT DISTINCT platform FROM accounts")
            platforms = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return platforms
    
    def get_accounts_by_platform(self, platform: str) -> List[Dict[str, Any]]:
        """获取指定平台的所有账号"""
        with self.lock:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM accounts WHERE platform=? ORDER BY name", (platform,))
            rows = cursor.fetchall()
            
            accounts = []
            for row in rows:
                account = dict(row)
                # 解析details字段
                if 'details' in account and account['details']:
                    try:
                        account['details'] = json.loads(account['details'])
                    except:
                        account['details'] = {}
                accounts.append(account)
            
            conn.close()
            return accounts 
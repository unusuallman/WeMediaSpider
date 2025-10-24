#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库ORM实现
=============

使用SQLAlchemy ORM的数据库实现。
"""

from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy import create_engine, and_, or_, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

from .models import Base, Account, Article
from spider.log.utils import logger


class DatabaseORM:
    """使用SQLAlchemy ORM的数据库实现"""

    def __init__(self, database_url: str):
        """
        初始化数据库

        Args:
            database_url: 数据库连接URL
        """
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # 初始化数据库表
        self.init_database()

    def init_database(self) -> None:
        """初始化数据库表结构"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info(f"数据库表初始化完成: {self.database_url}")
        except Exception as e:
            logger.error(f"数据库表初始化失败: {e}")
            raise

    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()

    def save_account(self,
                    name: str,
                    platform: str,
                    account_id: Optional[str] = None,
                    details: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        保存账号信息

        Args:
            name: 账号名称
            platform: 平台类型
            account_id: 平台上的账号ID
            details: 其他账号详情

        Returns:
            str: 数据库中的账号ID
        """
        session = self.get_session()
        try:
            # 检查账号是否已存在
            existing_account = session.query(Account).filter(
                and_(Account.platform == platform, Account.name == name)
            ).first()

            if existing_account:
                logger.info(f"账号已存在: {name}, {platform}, {account_id}")
                # 更新现有账号
                if details:
                    if existing_account.details is None:
                        existing_account.details.update({})
                    existing_account.details.update(details)
                # 使用 merge() 合并对象状态，flush() 同步到数据库
                session.merge(existing_account)
                session.flush()
                session.commit()
                return str(existing_account.id)
            else:
                logger.info(f"插入新账号: {name}, {platform}, {account_id}")
                # 创建新账号
                account = Account(
                    name=name,
                    platform=platform,
                    account_id=account_id or "",
                    details=details or {}
                )
                session.add(account)
                session.commit()
                return str(account.id)

        except IntegrityError as e:
            logger.error(f"保存账号失败 - 完整性错误: {e}, 账号: {name}, 平台: {platform}, ID: {account_id}")
            session.rollback()
            # 尝试获取现有账号
            existing = session.query(Account).filter(
                and_(Account.platform == platform, Account.name == name)
            ).first()
            if existing:
                return str(existing.id)
            return None
        except Exception as e:
            logger.error(f"保存账号失败: {e}, 账号: {name}, 平台: {platform}, ID: {account_id}")
            session.rollback()
            return None
        finally:
            session.close()

    def get_account(self,
                   id: Optional[str] = None,
                   name: Optional[str] = None,
                   platform: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取账号信息

        Args:
            id: 数据库中的账号ID
            name: 账号名称
            platform: 平台类型

        Returns:
            Dict: 账号信息
        """
        session = self.get_session()
        try:
            if id:
                account = session.query(Account).filter(Account.id == id).first()
            elif name and platform:
                account = session.query(Account).filter(
                    and_(Account.platform == platform, Account.name == name)
                ).first()
            else:
                return None

            if not account:
                return None

            return {
                'id': account.id,
                'name': account.name,
                'platform': account.platform,
                'account_id': account.account_id,
                'details': account.details,
                'created_at': account.created_at.isoformat() if account.created_at is not None else None,
                'updated_at': account.updated_at.isoformat() if account.updated_at is not None else None
            }

        except Exception as e:
            logger.error(f"获取账号失败: {e}")
            return None
        finally:
            session.close()

    def save_article(self,
                    account_id: str,
                    title: str,
                    url: str,
                    publish_time: Optional[str] = None,
                    content: Optional[str] = None,
                    details: Optional[Dict[str, Any]] = None,
                    summary: Optional[str] = None) -> bool:
        """
        保存文章

        Args:
            account_id: 账号ID
            title: 文章标题
            url: 文章URL
            publish_time: 发布时间
            content: 文章内容
            details: 其他详情
            summary: 文章摘要

        Returns:
            bool: 是否保存成功
        """
        session = self.get_session()
        try:
            # 检查文章是否已存在
            existing_article = session.query(Article).filter(Article.url == url).first()
            if existing_article:
                logger.info(f"文章已存在, title: {title}")
                return False

            # 计算发布时间戳
            publish_timestamp = 0
            if publish_time:
                try:
                    dt = datetime.strptime(publish_time, "%Y-%m-%d %H:%M:%S")
                    publish_timestamp = int(dt.timestamp())
                except Exception:
                    publish_timestamp = int(datetime.now().timestamp())

            # 创建新文章
            article = Article(
                account_id=int(account_id),
                title=title,
                url=url,
                publish_time=publish_time or "",
                publish_timestamp=publish_timestamp,
                content=content or "",
                summary=summary or "",
                details=details or {}
            )

            session.add(article)
            session.commit()
            logger.info(f"插入新文章, title: {title}")
            return True

        except Exception as e:
            logger.error(f"保存文章失败: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def get_articles(self,
                    account_id: Optional[str] = None,
                    platform: Optional[str] = None,
                    start_date: Optional[str] = None,
                    end_date: Optional[str] = None,
                    keywords: Optional[List[str]] = None,
                    limit: int = 100,
                    offset: int = 0) -> List[Dict[str, Any]]:
        """
        查询文章

        Args:
            account_id: 账号ID
            platform: 平台类型
            start_date: 开始日期
            end_date: 结束日期
            keywords: 关键词列表
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            List[Dict]: 文章列表
        """
        session = self.get_session()
        try:
            query = session.query(Article)

            if platform and not account_id:
                # 按平台查询, 需要join accounts表
                query = query.join(Account).filter(Account.platform == platform)
            elif account_id:
                query = query.filter(Article.account_id == account_id)

            # 日期过滤
            if start_date:
                start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
                query = query.filter(Article.publish_timestamp >= start_ts)

            if end_date:
                end_ts = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp()) + 86399
                query = query.filter(Article.publish_timestamp <= end_ts)

            # 关键词搜索
            if keywords:
                keyword_filters = []
                for keyword in keywords:
                    keyword_filters.append(Article.title.contains(keyword))
                    keyword_filters.append(Article.content.contains(keyword))
                    keyword_filters.append(Article.summary.contains(keyword))
                query = query.filter(or_(*keyword_filters))

            # 排序和分页
            articles = query.order_by(Article.publish_timestamp.desc()).limit(limit).offset(offset).all()

            result = []
            for article in articles:
                result.append({
                    'id': article.id,
                    'account_id': article.account_id,
                    'title': article.title,
                    'url': article.url,
                    'publish_time': article.publish_time,
                    'publish_timestamp': article.publish_timestamp,
                    'content': article.content,
                    'summary': article.summary,
                    'details': article.details,
                    'created_at': article.created_at.isoformat() if article.created_at is not None else None,
                    'updated_at': article.updated_at.isoformat() if article.updated_at is not None else None
                })

            return result

        except Exception as e:
            logger.error(f"查询文章失败: {e}")
            return []
        finally:
            session.close()

    def count_articles(self,
                      account_id: Optional[str] = None,
                      platform: Optional[str] = None) -> int:
        """
        统计文章数量

        Args:
            account_id: 账号ID
            platform: 平台类型

        Returns:
            int: 文章数量
        """
        session = self.get_session()
        try:
            query = session.query(func.count(Article.id))

            if platform and not account_id:
                query = query.join(Account).filter(Account.platform == platform)
            elif account_id:
                query = query.filter(Article.account_id == account_id)

            count = query.scalar()
            return count or 0

        except Exception as e:
            logger.error(f"统计文章数量失败: {e}")
            return 0
        finally:
            session.close()

    def get_article_by_id(self, article_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取单篇文章

        Args:
            article_id: 文章ID

        Returns:
            Dict[str, Any] or None: 文章信息, 不存在则返回None
        """
        session = self.get_session()
        try:
            article = session.query(Article).filter(Article.id == article_id).first()
            if not article:
                return None

            return {
                'id': article.id,
                'account_id': article.account_id,
                'title': article.title,
                'url': article.url,
                'publish_time': article.publish_time,
                'publish_timestamp': article.publish_timestamp,
                'content': article.content,
                'summary': article.summary,
                'details': article.details,
                'created_at': article.created_at.isoformat() if article.created_at is not None else None,
                'updated_at': article.updated_at.isoformat() if article.updated_at is not None else None
            }

        except Exception as e:
            logger.error(f"获取文章失败: {e}")
            return None
        finally:
            session.close()

    def update_article_summary(self, article_id: str, summary: str) -> bool:
        """
        更新文章摘要

        Args:
            article_id: 文章ID
            summary: 文章摘要内容

        Returns:
            bool: 更新是否成功
        """
        session = self.get_session()
        try:
            # 使用 update() 方法而不是直接赋值
            updated_rows = session.query(Article).filter(Article.id == article_id).update(
                {Article.summary: summary},
                synchronize_session=False
            )
            
            if updated_rows == 0:
                logger.error(f"文章不存在, 无法更新摘要: article_id={article_id}")
                return False

            session.commit()
            logger.info(f"成功更新文章摘要: article_id={article_id}")
            return True

        except Exception as e:
            logger.error(f"更新文章摘要失败: {e}, article_id={article_id}")
            session.rollback()
            return False
        finally:
            session.close()

    def get_article_summary(self, article_id: str) -> Optional[str]:
        """
        获取文章摘要

        Args:
            article_id: 文章ID

        Returns:
            Optional[str]: 文章摘要内容, 不存在则返回None
        """
        session = self.get_session()
        try:
            article = session.query(Article).filter(Article.id == article_id).first()
            if not article:
                logger.info(f"文章不存在, 无法获取摘要: article_id={article_id}")
                return None

            return str(article.summary) if article.summary is not None else None

        except Exception as e:
            logger.error(f"获取文章摘要失败: {e}, article_id={article_id}")
            return None
        finally:
            session.close()

    def get_platforms(self) -> List[str]:
        """
        获取所有平台类型

        Returns:
            List[str]: 平台类型列表
        """
        session = self.get_session()
        try:
            platforms = session.query(Account.platform).distinct().all()
            return [p[0] for p in platforms]

        except Exception as e:
            logger.error(f"获取平台列表失败: {e}")
            return []
        finally:
            session.close()

    def get_accounts_by_platform(self, platform: str) -> List[Dict[str, Any]]:
        """
        获取指定平台的所有账号

        Args:
            platform: 平台类型

        Returns:
            List[Dict]: 账号列表
        """
        session = self.get_session()
        try:
            accounts = session.query(Account).filter(Account.platform == platform).order_by(Account.name).all()

            result = []
            for account in accounts:
                result.append({
                    'id': account.id,
                    'name': account.name,
                    'platform': account.platform,
                    'account_id': account.account_id,
                    'details': account.details,
                    'created_at': account.created_at.isoformat() if account.created_at is not None else None,
                    'updated_at': account.updated_at.isoformat() if account.updated_at is not None else None
                })

            return result

        except Exception as e:
            logger.error(f"获取平台账号失败: {e}")
            return []
        finally:
            session.close()
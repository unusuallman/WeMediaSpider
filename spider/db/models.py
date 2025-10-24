#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库ORM模型
=============

使用SQLAlchemy定义的数据库模型。
"""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Account(Base):
    """账号模型"""
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    platform = Column(String(50), nullable=False)
    account_id = Column(String(255))
    details = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now())
    updated_at = Column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())

    # 关系
    articles = relationship("Article", back_populates="account")

    # 唯一约束
    __table_args__ = (
        Index('idx_accounts_platform_name', 'platform', 'name', unique=True),
        Index('idx_accounts_platform', 'platform'),
    )

    def __repr__(self):
        return f"<Account(id={self.id}, name='{self.name}', platform='{self.platform}')>"


class Article(Base):
    """文章模型"""
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False, unique=True)
    publish_time = Column(String(50))
    publish_timestamp = Column(Integer)
    content = Column(Text)
    summary = Column(Text)
    details = Column(JSON)  # 直接支持JSON类型
    created_at = Column(DateTime, default=lambda: datetime.now())
    updated_at = Column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())

    # 关系
    account = relationship("Account", back_populates="articles")

    # 索引
    __table_args__ = (
        Index('idx_articles_account', 'account_id'),
        Index('idx_articles_timestamp', 'publish_timestamp'),
    )

    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title[:50]}...')>"
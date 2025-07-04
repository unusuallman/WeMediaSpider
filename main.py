#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
内容爬虫主模块
======================

提供内容爬虫的通用入口，支持不同平台（微信、微博、知乎等）的爬虫功能。
可以通过命令行运行或作为库导入使用。

版本: 2.0
"""

import os
import sys
import argparse
from spider.log.utils import setup_logger, logger
# 目前只导入微信爬虫，后续可以添加其他平台的爬虫
from spider.wechat.run import WeChatSpiderRunner, login as wechat_login
from spider.wechat.run import search as wechat_search
from spider.wechat.run import scrape_account as wechat_scrape_account
from spider.wechat.run import batch_scrape as wechat_batch_scrape

# 未来可以导入其他平台的爬虫
# from spider.weibo.run import WeiboSpiderRunner
# from spider.zhihu.run import ZhiHuSpiderRunner


def main():
    """主函数，解析命令行参数并执行相应命令"""
    parser = argparse.ArgumentParser(description="内容爬虫工具")
    subparsers = parser.add_subparsers(dest="platform", help="选择平台")
    
    # 微信公众号爬虫
    wechat_parser = subparsers.add_parser("wechat", help="微信公众号爬虫")
    wechat_subparsers = wechat_parser.add_subparsers(dest="command", help="微信爬虫命令")
    
    # wechat login 命令
    wechat_login_parser = wechat_subparsers.add_parser("login", help="登录微信公众平台")
    wechat_login_parser.add_argument("--log-file", help="日志文件路径")
    wechat_login_parser.add_argument("--log-level", default="INFO", help="日志级别")
    
    # wechat search 命令
    wechat_search_parser = wechat_subparsers.add_parser("search", help="搜索公众号")
    wechat_search_parser.add_argument("name", help="公众号名称")
    wechat_search_parser.add_argument("-o", "--output", help="保存搜索结果的文件")
    wechat_search_parser.add_argument("--log-file", help="日志文件路径")
    wechat_search_parser.add_argument("--log-level", default="INFO", help="日志级别")
    
    # wechat single 命令
    wechat_single_parser = wechat_subparsers.add_parser("single", help="爬取单个公众号")
    wechat_single_parser.add_argument("name", help="公众号名称")
    wechat_single_parser.add_argument("-p", "--pages", type=int, default=10, help="最大爬取页数")
    wechat_single_parser.add_argument("-d", "--days", type=int, default=30, help="爬取最近几天的文章")
    wechat_single_parser.add_argument("-c", "--content", action="store_true", help="是否获取文章内容")
    wechat_single_parser.add_argument("-i", "--interval", type=int, default=10, help="请求间隔(秒)")
    wechat_single_parser.add_argument("-o", "--output", help="输出文件路径")
    wechat_single_parser.add_argument("--db", action="store_true", help="是否使用数据库")
    wechat_single_parser.add_argument("--db-type", default="sqlite", help="数据库类型(默认sqlite)")
    wechat_single_parser.add_argument("--log-file", help="日志文件路径")
    wechat_single_parser.add_argument("--log-level", default="INFO", help="日志级别")
    
    # wechat batch 命令
    wechat_batch_parser = wechat_subparsers.add_parser("batch", help="批量爬取多个公众号")
    wechat_batch_parser.add_argument("file", help="包含公众号列表的文件")
    wechat_batch_parser.add_argument("-p", "--pages", type=int, default=10, help="每个公众号最大爬取页数")
    wechat_batch_parser.add_argument("-d", "--days", type=int, default=30, help="爬取最近几天的文章")
    wechat_batch_parser.add_argument("-c", "--content", action="store_true", help="是否获取文章内容")
    wechat_batch_parser.add_argument("-i", "--interval", type=int, default=10, help="请求间隔(秒)")
    wechat_batch_parser.add_argument("-t", "--threads", type=int, default=3, help="线程数")
    wechat_batch_parser.add_argument("-o", "--output-dir", help="输出目录")
    wechat_batch_parser.add_argument("--db", action="store_true", help="是否使用数据库")
    wechat_batch_parser.add_argument("--db-type", default="sqlite", help="数据库类型(默认sqlite)")
    wechat_batch_parser.add_argument("--log-file", help="日志文件路径")
    wechat_batch_parser.add_argument("--log-level", default="INFO", help="日志级别")
    
    # 这里可以添加其他平台的爬虫，例如：
    # 微博爬虫
    # weibo_parser = subparsers.add_parser("weibo", help="微博爬虫")
    # weibo_subparsers = weibo_parser.add_subparsers(dest="command", help="微博爬虫命令")
    # ...
    
    # 知乎爬虫
    # zhihu_parser = subparsers.add_parser("zhihu", help="知乎爬虫")
    # zhihu_subparsers = zhihu_parser.add_subparsers(dest="command", help="知乎爬虫命令")
    # ...
    
    args = parser.parse_args()
    
    # 如果没有指定平台，显示帮助信息
    if not args.platform:
        parser.print_help()
        return 0
    
    # 配置日志
    log_file = getattr(args, 'log_file', None)
    log_level = getattr(args, 'log_level', "INFO")
    setup_logger(log_file, log_level)
    
    # 处理微信爬虫命令
    if args.platform == "wechat":
        return handle_wechat_commands(args)
    
    # 处理其他平台的爬虫命令
    # elif args.platform == "weibo":
    #     return handle_weibo_commands(args)
    # elif args.platform == "zhihu":
    #     return handle_zhihu_commands(args)
    else:
        logger.warning(f"未识别的平台: {args.platform}")
        parser.print_help()
        return 0


def handle_wechat_commands(args):
    """处理微信爬虫的命令"""
    if not args.command:
        logger.error("请指定微信爬虫的命令")
        return 1
    
    if args.command == "login":
        logger.info("准备登录微信公众平台...")
        return 0 if wechat_login() else 1
    elif args.command == "search":
        logger.info(f"搜索公众号: {args.name}")
        results = wechat_search(args.name, args.output)
        return 0 if results else 1
    elif args.command == "single":
        logger.info(f"开始爬取公众号: {args.name}")
        logger.debug(f"参数: 页数={args.pages}, 天数={args.days}, 获取内容={args.content}")
        return 0 if wechat_scrape_account(
            args.name,
            pages=args.pages,
            days=args.days,
            include_content=args.content,
            interval=args.interval,
            output_file=args.output,
            use_db=args.db,
            db_type=args.db_type
        ) else 1
    elif args.command == "batch":
        logger.info(f"开始批量爬取公众号, 来源文件: {args.file}")
        logger.debug(f"参数: 页数={args.pages}, 天数={args.days}, 获取内容={args.content}, 线程数={args.threads}")
        return 0 if wechat_batch_scrape(
            args.file,
            pages=args.pages,
            days=args.days,
            include_content=args.content,
            interval=args.interval,
            threads=args.threads,
            output_dir=args.output_dir,
            use_db=args.db,
            db_type=args.db_type
        ) else 1
    else:
        logger.error(f"未知的微信爬虫命令: {args.command}")
        return 1


# 可以添加处理其他平台爬虫命令的函数
# def handle_weibo_commands(args):
#     """处理微博爬虫的命令"""
#     ...
#
# def handle_zhihu_commands(args):
#     """处理知乎爬虫的命令"""
#     ...


# 示例使用方法
def example_usage():
    """示例：如何在代码中使用爬虫模块"""
    # 微信爬虫示例
    logger.info("=== 微信爬虫使用示例 ===")
    wechat_runner = WeChatSpiderRunner()
    
    # 登录
    if not wechat_runner.login():
        logger.error("微信登录失败")
        return False
    
    # 搜索公众号
    accounts = wechat_runner.search_account("腾讯科技")
    if not accounts:
        logger.warning("未找到匹配的微信公众号")
        return False
    
    # 爬取单个公众号
    logger.info("开始爬取腾讯科技公众号")
    wechat_runner.scrape_single_account(
        "腾讯科技",
        pages=5,
        days=7,
        include_content=True,
        output_file="腾讯科技.csv"
    )
    
    # 未来可以添加其他平台的爬虫示例
    # logger.info("=== 微博爬虫使用示例 ===")
    # weibo_runner = WeiboSpiderRunner()
    # ...
    
    # logger.info("=== 知乎爬虫使用示例 ===")
    # zhihu_runner = ZhiHuSpiderRunner()
    # ...
    
    return True


if __name__ == "__main__":
    main()

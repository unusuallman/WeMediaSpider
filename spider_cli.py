#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
微信公众号爬虫命令行工具
======================

为微信公众号爬虫提供命令行界面，支持登录、单个公众号爬取和批量爬取功能。
通过命令行参数配置爬虫行为，方便自动化和脚本化使用。

使用方法:
    python spider_cli.py login  # 登录并获取token和cookie
    python spider_cli.py search <公众号名称>  # 搜索公众号
    python spider_cli.py single <公众号名称> [选项]  # 爬取单个公众号
    python spider_cli.py batch <公众号列表文件> [选项]  # 批量爬取多个公众号

版本: 1.0
"""

import os
import sys
import argparse
import time
import json
from datetime import datetime, timedelta

# 导入爬虫模块
from src.login import WeChatSpiderLogin, quick_login
from src.scraper import WeChatScraper, BatchScraper
from src.database import ArticleDatabase
from src.utils import save_to_csv


def login_command():
    """登录命令，获取并保存token和cookie"""
    print("正在登录微信公众平台...")
    token, cookies, headers = quick_login()
    
    if not token or not cookies or not headers:
        print("登录失败")
        sys.exit(1)
    
    print(f"登录成功！")
    print(f"Token: {token[:8]}...{token[-4:]}")
    print(f"Cookie: {len(headers['cookie'])} 个字符")
    print("登录信息已保存到缓存文件")
    
    return 0


def search_command(args):
    """搜索公众号命令"""
    print(f"搜索公众号: {args.name}")
    
    # 创建登录管理器
    login_manager = WeChatSpiderLogin()
    if not login_manager.is_logged_in():
        print("未登录或登录已过期，请先登录")
        sys.exit(1)
    
    token = login_manager.get_token()
    headers = login_manager.get_headers()
    
    # 创建爬虫实例
    scraper = WeChatScraper(token, headers)
    
    # 搜索公众号
    results = scraper.search_account(args.name)
    
    if not results:
        print(f"未找到匹配的公众号: {args.name}")
        return 1
    
    print(f"找到 {len(results)} 个匹配的公众号:")
    for i, account in enumerate(results):
        print(f"{i+1}. {account['wpub_name']} (fakeid: {account['wpub_fakid']})")
    
    # 保存结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"搜索结果已保存到: {args.output}")
    
    return 0


def single_command(args):
    """单个公众号爬取命令"""
    print(f"爬取公众号: {args.name}")
    
    # 创建登录管理器
    login_manager = WeChatSpiderLogin()
    if not login_manager.is_logged_in():
        print("未登录或登录已过期，请先登录")
        sys.exit(1)
    
    token = login_manager.get_token()
    headers = login_manager.get_headers()
    
    # 创建爬虫实例
    scraper = WeChatScraper(token, headers)
    
    # 搜索公众号
    print(f"搜索公众号: {args.name}")
    results = scraper.search_account(args.name)
    
    if not results:
        print(f"未找到匹配的公众号: {args.name}")
        return 1
    
    # 使用第一个匹配结果
    account = results[0]
    print(f"使用公众号: {account['wpub_name']} (fakeid: {account['wpub_fakid']})")
    
    # 进度回调
    def progress_callback(current, total):
        print(f"进度: {current}/{total} 页")
    
    scraper.set_callback('progress', progress_callback)
    
    # 获取文章列表
    print(f"获取文章列表，最大 {args.pages} 页...")
    articles = scraper.get_account_articles(
        account['wpub_name'],
        account['wpub_fakid'],
        args.pages
    )
    
    print(f"获取到 {len(articles)} 篇文章")
    
    # 按日期过滤
    if args.days:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=args.days)
        
        print(f"过滤日期范围: {start_date} 至 {end_date}")
        filtered_articles = scraper.filter_articles_by_date(articles, start_date, end_date)
        print(f"过滤后剩余 {len(filtered_articles)} 篇文章")
    else:
        filtered_articles = articles
    
    # 获取文章内容
    if args.content:
        print("获取文章内容...")
        for i, article in enumerate(filtered_articles):
            print(f"获取第 {i+1}/{len(filtered_articles)} 篇文章内容...")
            article = scraper.get_article_content_by_url(article)
            
            # 请求间隔，避免被限制
            if i < len(filtered_articles) - 1:
                time.sleep(args.interval)
    
    # 保存结果
    if args.output:
        output_file = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{account['wpub_name']}_{timestamp}.csv"
    
    print(f"保存结果到: {output_file}")
    success = scraper.save_articles_to_csv(filtered_articles, output_file)
    
    if success:
        print(f"成功保存 {len(filtered_articles)} 篇文章")
    else:
        print("保存失败")
        return 1
    
    return 0


def batch_command(args):
    """批量爬取命令"""
    print(f"批量爬取公众号，输入文件: {args.file}")
    
    # 读取公众号列表
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 支持多种分隔符：换行、逗号、分号
        import re
        accounts = re.split(r'[\n\r,;，；、\s\t|]+', content.strip())
        accounts = [acc.strip() for acc in accounts if acc.strip()]
    except Exception as e:
        print(f"读取公众号列表失败: {str(e)}")
        return 1
    
    if not accounts:
        print("公众号列表为空")
        return 1
    
    print(f"共读取 {len(accounts)} 个公众号")
    
    # 创建登录管理器
    login_manager = WeChatSpiderLogin()
    if not login_manager.is_logged_in():
        print("未登录或登录已过期，请先登录")
        sys.exit(1)
    
    token = login_manager.get_token()
    headers = login_manager.get_headers()
    
    # 创建批量爬虫实例
    batch_scraper = BatchScraper()
    
    # 设置回调函数
    def progress_callback(batch_id, current, total):
        print(f"批次 {batch_id}: {current}/{total} 公众号")
    
    def account_status_callback(account_name, status, message):
        print(f"{account_name}: {message}")
    
    def batch_completed_callback(batch_id, total_articles):
        print(f"批次 {batch_id} 完成，共获取 {total_articles} 篇文章")
    
    def error_callback(account_name, error_message):
        print(f"错误 - {account_name}: {error_message}")
    
    batch_scraper.set_callback('progress_updated', progress_callback)
    batch_scraper.set_callback('account_status', account_status_callback)
    batch_scraper.set_callback('batch_completed', batch_completed_callback)
    batch_scraper.set_callback('error_occurred', error_callback)
    
    # 计算时间范围
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=args.days)
    
    # 确保输出目录存在
    output_dir = args.output_dir or "results"
    os.makedirs(output_dir, exist_ok=True)
    
    # 准备配置
    timestamp = int(time.time())
    config = {
        'accounts': accounts,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'token': token,
        'headers': headers,
        'batch_id': f"batch_{timestamp}",
        'max_pages_per_account': args.pages,
        'request_interval': args.interval,
        'use_threading': args.threads > 1,
        'max_workers': args.threads,
        'include_content': args.content,
        'use_database': args.db,
        'db_file': os.path.join(output_dir, "wechat_articles.db"),
        'output_file': os.path.join(output_dir, f"batch_articles_{timestamp}.csv")
    }
    
    # 开始爬取
    print("\n开始批量爬取...")
    print(f"时间范围: {start_date} 至 {end_date}")
    print(f"每个公众号最多爬取 {args.pages} 页")
    print(f"请求间隔: {args.interval} 秒")
    
    start_time = time.time()
    articles = batch_scraper.start_batch_scrape(config)
    end_time = time.time()
    
    print(f"\n爬取完成，耗时 {end_time - start_time:.2f} 秒")
    print(f"共获取 {len(articles)} 篇文章，已保存到 {config['output_file']}")
    
    if args.db:
        print(f"数据库文件: {config['db_file']}")
    
    return 0


def main():
    """主函数，解析命令行参数并执行相应命令"""
    parser = argparse.ArgumentParser(description="微信公众号爬虫命令行工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # login 命令
    login_parser = subparsers.add_parser("login", help="登录微信公众平台")
    
    # search 命令
    search_parser = subparsers.add_parser("search", help="搜索公众号")
    search_parser.add_argument("name", help="公众号名称")
    search_parser.add_argument("-o", "--output", help="保存搜索结果的文件")
    
    # single 命令
    single_parser = subparsers.add_parser("single", help="爬取单个公众号")
    single_parser.add_argument("name", help="公众号名称")
    single_parser.add_argument("-p", "--pages", type=int, default=10, help="最大爬取页数")
    single_parser.add_argument("-d", "--days", type=int, default=30, help="爬取最近几天的文章")
    single_parser.add_argument("-c", "--content", action="store_true", help="是否获取文章内容")
    single_parser.add_argument("-i", "--interval", type=int, default=10, help="请求间隔(秒)")
    single_parser.add_argument("-o", "--output", help="输出文件路径")
    
    # batch 命令
    batch_parser = subparsers.add_parser("batch", help="批量爬取多个公众号")
    batch_parser.add_argument("file", help="包含公众号列表的文件")
    batch_parser.add_argument("-p", "--pages", type=int, default=10, help="每个公众号最大爬取页数")
    batch_parser.add_argument("-d", "--days", type=int, default=30, help="爬取最近几天的文章")
    batch_parser.add_argument("-c", "--content", action="store_true", help="是否获取文章内容")
    batch_parser.add_argument("-i", "--interval", type=int, default=10, help="请求间隔(秒)")
    batch_parser.add_argument("-t", "--threads", type=int, default=3, help="线程数")
    batch_parser.add_argument("-o", "--output-dir", help="输出目录")
    batch_parser.add_argument("--db", action="store_true", help="是否使用数据库")
    
    args = parser.parse_args()
    
    if args.command == "login":
        return login_command()
    elif args.command == "search":
        return search_command(args)
    elif args.command == "single":
        return single_command(args)
    elif args.command == "batch":
        return batch_command(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main()) 
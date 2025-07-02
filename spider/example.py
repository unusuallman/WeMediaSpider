#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
微信公众号爬虫 - 示例脚本
======================

展示如何使用爬虫模块进行微信公众号文章爬取的示例。
提供了单个爬取和批量爬取的使用方法。

使用方法:
    1. 确保已安装所需依赖（见requirements.txt）
    2. 运行此脚本进行爬虫演示
    3. 根据需要修改配置参数

版本: 1.0
"""

import os
import time
from datetime import datetime, timedelta

from login import WeChatSpiderLogin, quick_login
from scraper import WeChatScraper, BatchScraper
from database import ArticleDatabase


def example_single_account():
    """单个公众号爬取示例"""
    print("\n===== 单个公众号爬取示例 =====")
    
    # 第一步：登录获取token和cookie
    print("\n[1] 登录获取token和cookie...")
    token, cookies, headers = quick_login()
    
    if not token or not cookies:
        print("登录失败，请检查网络连接或重试")
        return
    
    # 第二步：创建爬虫实例
    print("\n[2] 创建爬虫实例...")
    scraper = WeChatScraper(token, headers)
    
    # 第三步：搜索公众号
    print("\n[3] 搜索公众号...")
    account_name = input("请输入要爬取的公众号名称: ")
    search_results = scraper.search_account(account_name)
    
    if not search_results:
        print(f"未找到公众号: {account_name}")
        return
    
    print(f"找到 {len(search_results)} 个匹配的公众号:")
    for i, account in enumerate(search_results):
        print(f"  {i+1}. {account['wpub_name']} (fakeid: {account['wpub_fakid']})")
    
    # 选择公众号
    selected_index = 0
    if len(search_results) > 1:
        selected_index = int(input(f"请选择要爬取的公众号 (1-{len(search_results)}): ")) - 1
    
    selected_account = search_results[selected_index]
    print(f"已选择公众号: {selected_account['wpub_name']}")
    
    # 第四步：获取文章列表
    print("\n[4] 获取文章列表...")
    max_pages = int(input("请输入要爬取的最大页数 (每页5篇文章): "))
    
    # 设置进度回调
    def progress_callback(current, total):
        print(f"进度: {current}/{total} 页")
    
    scraper.set_callback('progress', progress_callback)
    
    articles = scraper.get_account_articles(
        selected_account['wpub_name'],
        selected_account['wpub_fakid'],
        max_pages
    )
    
    print(f"获取到 {len(articles)} 篇文章")
    
    # 第五步：按日期筛选
    print("\n[5] 按日期筛选文章...")
    days_ago = int(input("要筛选最近几天的文章? "))
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days_ago)
    
    filtered_articles = scraper.filter_articles_by_date(articles, start_date, end_date)
    print(f"日期范围 {start_date} 到 {end_date} 内有 {len(filtered_articles)} 篇文章")
    
    # 第六步：获取文章内容
    print("\n[6] 获取文章内容...")
    get_content = input("是否获取文章内容? (y/n): ").lower() == 'y'
    
    if get_content:
        print("正在获取文章内容，这可能需要一些时间...")
        
        for i, article in enumerate(filtered_articles):
            print(f"获取第 {i+1}/{len(filtered_articles)} 篇文章内容...")
            article = scraper.get_article_content_by_url(article)
            # 请求间隔，避免被限制
            if i < len(filtered_articles) - 1:
                time.sleep(2)
    
    # 第七步：保存结果
    print("\n[7] 保存结果...")
    save_dir = "results"
    os.makedirs(save_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(save_dir, f"{selected_account['wpub_name']}_{timestamp}.csv")
    
    saved = scraper.save_articles_to_csv(filtered_articles, filename)
    
    if saved:
        print(f"文章已保存到: {filename}")
    else:
        print("保存失败")


def example_batch_scrape():
    """批量爬取示例"""
    print("\n===== 批量爬取示例 =====")
    
    # 第一步：登录获取token和cookie
    print("\n[1] 登录获取token和cookie...")
    token, cookies, headers = quick_login()
    
    if not token or not cookies:
        print("登录失败，请检查网络连接或重试")
        return
    
    # 第二步：创建批量爬虫实例
    print("\n[2] 创建批量爬虫实例...")
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
    
    # 第三步：准备配置
    print("\n[3] 准备爬取配置...")
    
    # 公众号列表
    accounts_input = input("请输入要爬取的公众号名称（多个用逗号分隔）: ")
    accounts = [acc.strip() for acc in accounts_input.split(",")]
    print(f"将爬取 {len(accounts)} 个公众号: {', '.join(accounts)}")
    
    # 时间范围
    days_ago = int(input("要爬取最近几天的文章? "))
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days_ago)
    
    # 爬取配置
    config = {
        'accounts': accounts,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'token': token,
        'headers': headers,
        'batch_id': f"batch_{int(time.time())}",
        'max_pages_per_account': 10,  # 每个公众号最多爬取的页数
        'request_interval': 5,  # 请求间隔（秒）
        'account_interval': (10, 15),  # 账号间隔范围（秒）
        'use_threading': len(accounts) > 1,  # 是否使用多线程
        'max_workers': min(3, len(accounts)),  # 最大线程数
        'include_content': True,  # 是否获取文章内容
        'use_database': True,  # 是否使用数据库
        'db_file': os.path.join("results", "wechat_articles.db"),  # 数据库文件
        'output_file': os.path.join("results", f"batch_articles_{int(time.time())}.csv")  # 输出文件
    }
    
    # 确保目录存在
    os.makedirs(os.path.dirname(config['db_file']), exist_ok=True)
    os.makedirs(os.path.dirname(config['output_file']), exist_ok=True)
    
    # 第四步：开始爬取
    print("\n[4] 开始批量爬取...")
    
    start_time = time.time()
    articles = batch_scraper.start_batch_scrape(config)
    end_time = time.time()
    
    print(f"\n爬取完成，耗时 {end_time - start_time:.2f} 秒")
    print(f"共获取 {len(articles)} 篇文章，已保存到 {config['output_file']}")
    print(f"数据库文件: {config['db_file']}")


def example_query_database():
    """数据库查询示例"""
    print("\n===== 数据库查询示例 =====")
    
    db_file = input("请输入数据库文件路径 (默认: results/wechat_articles.db): ")
    if not db_file:
        db_file = "results/wechat_articles.db"
    
    if not os.path.exists(db_file):
        print(f"数据库文件不存在: {db_file}")
        return
    
    # 创建数据库实例
    db = ArticleDatabase(db_file)
    
    # 查询批次信息
    print("\n批次信息:")
    batches = db.get_batch_info()
    
    if not batches:
        print("没有找到批次信息")
        return
    
    for i, batch in enumerate(batches):
        print(f"{i+1}. 批次ID: {batch['batch_id']}")
        print(f"   开始日期: {batch['start_date']}，结束日期: {batch['end_date']}")
        print(f"   公众号数: {len(batch['accounts'])}，文章数: {batch['total_articles']}")
        print(f"   状态: {batch['status']}")
        print()
    
    # 查询公众号列表
    print("\n公众号列表:")
    accounts = db.get_unique_accounts()
    for account in accounts:
        count = db.count_articles(account_name=account)
        print(f"{account}: {count} 篇文章")
    
    # 按条件查询文章
    print("\n按条件查询文章:")
    account_name = input("公众号名称 (留空则查询全部): ")
    keywords = input("关键词 (多个用逗号分隔，留空则不过滤): ")
    limit = int(input("返回条数上限 (默认20): ") or "20")
    
    keyword_list = [k.strip() for k in keywords.split(",")] if keywords else None
    
    # 查询文章
    articles = db.get_articles(
        account_name=account_name if account_name else None,
        keywords=keyword_list,
        limit=limit
    )
    
    print(f"\n找到 {len(articles)} 篇文章:")
    for i, article in enumerate(articles):
        print(f"{i+1}. {article['title']}")
        print(f"   公众号: {article['account_name']}")
        print(f"   发布时间: {article['publish_time']}")
        print(f"   链接: {article['link']}")
        print()


if __name__ == "__main__":
    print("微信公众号爬虫示例程序")
    print("=" * 40)
    print("1. 单个公众号爬取示例")
    print("2. 批量爬取示例")
    print("3. 数据库查询示例")
    print("0. 退出")
    print("=" * 40)
    
    choice = input("请选择要运行的示例 (0-3): ")
    
    if choice == "1":
        example_single_account()
    elif choice == "2":
        example_batch_scrape()
    elif choice == "3":
        example_query_database()
    else:
        print("退出程序") 
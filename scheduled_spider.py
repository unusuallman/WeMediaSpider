#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
定时爬虫脚本
======================

使用schedule库实现每天9点自动爬取accounts.txt中配置的公众号列表中的文章

使用方法:
1. 在accounts.txt中添加要爬取的公众号名称，每行一个
2. 直接运行此脚本: python scheduled_spider.py
3. 要立即执行爬取任务，使用: python scheduled_spider.py --now

版本: 1.0
"""

import os
import sys
import time
import datetime
import logging
import schedule
from pathlib import Path

# 导入爬虫功能
from spider.log.utils import setup_logger, logger
from spider.wechat.run import login as wechat_login
from spider.wechat.run import batch_scrape as wechat_batch_scrape

# 配置参数
CONFIG = {
    "accounts_file": "accounts.txt",  # 公众号列表文件
    "pages": 1,                      # 每个公众号最大爬取页数
    "days": 1,                       # 爬取最近几天的文章（设为1表示只爬取当天）
    "include_content": True,         # 是否获取文章内容
    "interval": 20,                  # 请求间隔(秒)
    "threads": 3,                    # 线程数
    "output_dir": "output",          # 输出目录
    "use_db": True,                  # 是否使用数据库
    "db_type": "sqlite",             # 数据库类型
    "log_file": "logs/scheduled_spider.log", # 日志文件路径
    "log_level": "INFO",             # 日志级别
    "schedule_time": "14:30",        # 定时任务执行时间 (24小时制)
}

def setup_environment():
    """初始化环境，创建必要的目录"""
    # 创建日志目录
    log_dir = os.path.dirname(CONFIG["log_file"])
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 创建输出目录
    if CONFIG["output_dir"] and not os.path.exists(CONFIG["output_dir"]):
        os.makedirs(CONFIG["output_dir"])
    
    # 配置日志
    setup_logger(CONFIG["log_file"], CONFIG["log_level"])

def check_accounts_file():
    """检查公众号列表文件是否存在"""
    if not os.path.exists(CONFIG["accounts_file"]):
        logger.error(f"公众号列表文件不存在: {CONFIG['accounts_file']}")
        return False
    return True

def run_spider():
    """运行爬虫任务"""
    current_time = datetime.datetime.now()
    logger.info(f"开始定时爬取任务 - {current_time}")
    
    # 检查公众号列表文件
    if not check_accounts_file():
        return False
    
    # 登录微信公众平台
    logger.info("登录微信公众平台...")
    if not wechat_login():
        logger.error("微信登录失败，任务终止")
        return False
    
    # 批量爬取公众号
    logger.info(f"开始批量爬取公众号，来源文件: {CONFIG['accounts_file']}")
    result = wechat_batch_scrape(
        CONFIG["accounts_file"],
        pages=CONFIG["pages"],
        days=CONFIG["days"],
        include_content=CONFIG["include_content"],
        interval=CONFIG["interval"],
        threads=CONFIG["threads"],
        output_dir=CONFIG["output_dir"],
        use_db=CONFIG["use_db"],
        db_type=CONFIG["db_type"]
    )
    
    if result:
        logger.info("爬取任务完成")
        next_run = schedule.next_run()
        if next_run:
            logger.info(f"下次执行时间: {next_run}")
    else:
        logger.error("爬取任务失败")
    
    return result

def setup_schedule():
    """设置定时任务计划"""
    # 使用配置中的时间设置定时任务
    schedule.every().day.at(CONFIG["schedule_time"]).do(run_spider)
    logger.info(f"已设置定时任务: 每天{CONFIG['schedule_time']}执行爬取")
    
    # 显示下次执行时间
    next_run = schedule.next_run()
    if next_run:
        logger.info(f"下次执行时间: {next_run}")
        wait_seconds = (next_run - datetime.datetime.now()).total_seconds()
        logger.info(f"距离下次执行还有 {wait_seconds/3600:.2f} 小时")

def main():
    """主函数"""
    setup_environment()
    logger.info("定时爬虫启动")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--now":
        # 立即执行爬取任务
        logger.info("立即执行爬取任务")
        run_spider()
    
    # 设置定时任务计划
    setup_schedule()
    
    # 无限循环，运行所有计划任务
    logger.info("进入任务循环等待...")
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main() 
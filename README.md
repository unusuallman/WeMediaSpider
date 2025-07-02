# 微信公众号爬虫模块

这是一个专门用于爬取微信公众号文章的Python模块，提供了完整的功能集，从登录、搜索公众号到批量爬取文章内容。该模块不依赖于GUI界面，可以作为独立的库在任何Python项目中使用。

## 主要功能

- **自动登录**: 使用Selenium自动登录微信公众平台，获取token和cookie
- **公众号搜索**: 根据名称搜索匹配的公众号
- **文章列表获取**: 批量获取公众号的历史文章列表
- **文章内容爬取**: 抓取文章的完整内容
- **日期过滤**: 根据发布日期筛选文章
- **数据存储**: 支持CSV和SQLite数据库存储
- **多线程支持**: 可选的多线程并发爬取功能
- **断点续爬**: 支持中断后继续爬取
- **命令行接口**: 提供便捷的命令行工具
- **markdown转换**: 支持将爬取的HTML转为markdown格式

## 安装方法

1. 克隆仓库:

```bash
git clone https://github.com/seanzhang-zhichen/wechat_spider.git
```

2. 安装依赖:

```bash
pip install -r requirements.txt
```

## 目录结构

```
spider/
  ├── __init__.py         # 包初始化文件
  ├── login.py            # 登录功能模块
  ├── scraper.py          # 爬虫核心模块
  ├── database.py         # 数据库管理模块
  ├── utils.py            # 工具函数模块
  ├── example.py          # 示例使用脚本
  └── README.md           # 说明文档
```

## 使用方法

### 基本使用

```python
from spider.login import WeChatSpiderLogin, quick_login
from spider.scraper import WeChatScraper

# 1. 登录获取token和cookie
token, cookies, headers = quick_login()

# 2. 创建爬虫实例
scraper = WeChatScraper(token, headers)

# 3. 搜索公众号
results = scraper.search_account("公众号名称")
fakeid = results[0]['wpub_fakid']

# 4. 获取文章列表
articles = scraper.get_account_articles("公众号名称", fakeid, max_pages=10)

# 5. 获取文章内容
for article in articles[:5]:  # 获取前5篇文章的内容
    article = scraper.get_article_content_by_url(article)
    print(f"标题: {article['title']}")
    print(f"内容长度: {len(article['content'])}")

# 6. 保存结果
scraper.save_articles_to_csv(articles, "articles.csv")
```

### 批量爬取

```python
from spider.login import quick_login
from spider.scraper import BatchScraper

# 1. 登录获取token和cookie
token, cookies, headers = quick_login()

# 2. 创建批量爬虫实例
batch_scraper = BatchScraper()

# 3. 设置回调函数
def progress_callback(batch_id, current, total):
    print(f"进度: {current}/{total}")

batch_scraper.set_callback('progress_updated', progress_callback)

# 4. 准备配置
config = {
    'accounts': ["公众号1", "公众号2", "公众号3"],
    'start_date': "2023-01-01",
    'end_date': "2023-12-31",
    'token': token,
    'headers': headers,
    'max_pages_per_account': 10,
    'use_threading': True,
    'max_workers': 3,
    'include_content': True,
    'use_database': True,
    'db_file': "articles.db",
    'output_file': "batch_articles.csv"
}

# 5. 开始爬取
articles = batch_scraper.start_batch_scrape(config)
```

### 数据库操作

```python
from spider.database import ArticleDatabase

# 创建数据库实例
db = ArticleDatabase("articles.db")

# 查询文章
articles = db.get_articles(
    account_name="公众号名称",
    start_date="2023-01-01",
    end_date="2023-12-31",
    keywords=["关键词1", "关键词2"],
    limit=100
)

# 获取唯一公众号列表
accounts = db.get_unique_accounts()
```

## 命令行工具

项目根目录下提供了命令行工具 `spider_cli.py`:

```bash
# 登录
python spider_cli.py login

# 搜索公众号
python spider_cli.py search "公众号名称"

# 爬取单个公众号
python spider_cli.py single "公众号名称" --pages 10 --days 30 --content

# 批量爬取
python spider_cli.py batch accounts.txt --pages 10 --days 30 --content --db
```

使用 `python spider_cli.py --help` 查看完整帮助信息。

## 注意事项

1. **请求间隔**: 建议将请求间隔设置为适当的值（如5秒以上），避免被微信公众平台限制访问。
2. **登录缓存**: 登录信息会缓存到本地文件，有效期为4天，期间可重复使用而无需重新登录。
3. **数据库存储**: 建议启用数据库存储，便于后续查询和分析。
4. **多线程限制**: 过多的线程可能导致账号被限制，建议将`max_workers`控制在3-5之间。

## 依赖项

- Python 3.6+
- requests
- selenium
- beautifulsoup4
- tqdm
- pandas

详见 `requirements.txt`。

## 许可证

MIT License 
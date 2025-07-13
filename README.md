# 内容爬虫工具

这是一个用于爬取多平台内容的Python工具，目前主要支持微信公众号文章爬取，提供了完整的功能集，包括登录、搜索公众号、批量爬取文章内容等。该工具可以通过命令行使用，也可以作为独立的库在任何Python项目中导入使用。

## 版本说明

当前版本为 2.0，相比早期版本有以下改进：

- 重构了项目结构，将main.py移至根目录，便于命令行直接调用
- 完善了包结构，支持作为Python包导入使用
- 优化了数据库接口，提供工厂模式创建数据库实例
- 增强了日志系统，支持可配置的日志级别和输出方式
- 项目架构设计为支持多平台内容爬取（目前实现了微信公众号，后续将支持微博、知乎等平台）

## 主要功能

- **自动登录**: 使用Selenium自动登录微信公众平台，获取token和cookie
- **公众号搜索**: 根据名称搜索匹配的公众号
- **文章列表获取**: 批量获取公众号的历史文章列表
- **文章内容爬取**: 抓取文章的完整内容
- **日期过滤**: 根据发布日期筛选文章
- **数据存储**: 支持CSV和多种数据库存储（SQLite、MySQL等）
- **多平台支持**: 架构设计支持多平台内容爬取（目前主要支持微信）
- **多线程支持**: 可选的多线程并发爬取功能
- **断点续爬**: 支持中断后继续爬取
- **命令行接口**: 提供便捷的命令行工具
- **markdown转换**: 支持将爬取的HTML转为markdown格式
- **定时爬取**: 支持每两小时定时自动爬取公众号文章

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
wechat_spider/
  ├── main.py                # 主模块和命令行入口
  ├── README.md              # 说明文档
  ├── requirements.txt       # 依赖文件
  ├── scheduled_spider.py    # 定时爬虫脚本
  └── spider/                # 爬虫主目录
      ├── __init__.py        # 包初始化文件
      ├── db/                # 数据库相关模块
      │   ├── __init__.py    # 包初始化文件
      │   ├── factory.py     # 数据库工厂类
      │   ├── interface.py   # 数据库接口定义
      │   ├── mysql.py       # MySQL数据库实现
      │   └── sqlite.py      # SQLite数据库实现
      ├── log/               # 日志相关模块
      │   ├── __init__.py    # 包初始化文件
      │   └── utils.py       # 日志工具函数
      └── wechat/            # 微信爬虫专用模块
          ├── __init__.py    # 包初始化文件
          ├── login.py       # 登录功能模块
          ├── run.py         # 运行管理模块
          ├── scraper.py     # 爬虫核心模块
          └── utils.py       # 工具函数模块
```

## 使用方法

### 命令行使用

项目提供了命令行工具 `main.py`:

```bash
# 登录微信公众平台
python main.py wechat login

# 搜索公众号
python main.py wechat search "公众号名称" -o "结果保存路径.json"

# 爬取单个公众号
python main.py wechat single "公众号名称" -p 10 -d 30 -c -o "结果保存路径.csv" --db

# 批量爬取多个公众号
python main.py wechat batch "账号列表文件.txt" -p 10 -d 30 -c -t 3 -o "输出目录" --db
```

使用 `python main.py --help` 查看完整帮助信息。

### 定时爬虫使用

项目提供了定时爬虫脚本 `scheduled_spider.py`，用于每两小时自动爬取公众号文章：

#### 准备工作

1. 安装schedule库（如果未安装）:
```bash
pip install schedule
```

2. 创建`accounts.txt`文件，每行写入一个要爬取的公众号名称：
```
腾讯科技
新浪科技
36氪
...
```

#### 启动定时爬虫

直接运行脚本启动定时任务：
```bash
python scheduled_spider.py
```

脚本会使用Python的schedule库设置定时任务，默认每两小时自动执行爬取任务。脚本会保持运行并在后台等待执行时间。

如果想立即执行爬取任务（不等待到设定时间），可以使用以下命令：
```bash
python scheduled_spider.py --now
```

#### 配置参数

定时爬虫的默认配置可以在`scheduled_spider.py`文件中的`CONFIG`字典中修改，包括：

- `accounts_file`: 公众号列表文件
- `pages`: 每个公众号最大爬取页数
- `days`: 爬取最近几天的文章
- `include_content`: 是否获取文章内容
- `interval`: 请求间隔(秒)
- `threads`: 线程数
- `output_dir`: 输出目录
- `use_db`: 是否使用数据库
- `db_type`: 数据库类型
- `log_file`: 日志文件路径
- `log_level`: 日志级别
- `schedule_interval`: 定时任务执行间隔(小时)，默认为2小时

#### 在生产环境中运行

在生产环境中，建议将定时爬虫作为服务在后台运行：

**Windows系统**:
使用nssm工具将Python脚本注册为Windows服务

**Linux/MacOS系统**:
创建systemd服务或使用screen/tmux在后台运行：

```bash
# 使用screen创建会话
screen -S wechat_spider
# 在screen会话中运行脚本
python scheduled_spider.py
# 按Ctrl+A, 然后按D分离会话
```

### 作为库使用

```python
from spider.wechat.run import WeChatSpiderRunner

# 创建爬虫实例
wechat_runner = WeChatSpiderRunner()

# 登录
if not wechat_runner.login():
    print("微信登录失败")
    exit(1)

# 搜索公众号
accounts = wechat_runner.search_account("腾讯科技")
if not accounts:
    print("未找到匹配的微信公众号")
    exit(1)

# 爬取单个公众号
wechat_runner.scrape_single_account(
    "腾讯科技",
    pages=5,
    days=7,
    include_content=True,
    output_file="腾讯科技.csv"
)
```

## 数据库使用

```python
from spider.db.factory import DatabaseFactory

# 创建数据库实例 - SQLite (默认)
db = DatabaseFactory.create_database('sqlite', db_file="articles.db")

# 创建数据库实例 - MySQL
# db = DatabaseFactory.create_database('mysql', host="localhost", user="root", password="password", database="articles")

# 保存账号
account_id = db.save_account(
    name="公众号名称",
    platform="wechat",
    account_id="fakeid"
)

# 保存文章
db.save_article(
    account_id=account_id,
    title="文章标题",
    url="文章链接",
    publish_time="2023-01-01 12:00:00",
    content="文章内容",
    details={"digest": "摘要", "publish_timestamp": 1672531200}
)

# 查询文章
articles = db.get_articles(
    account_id=account_id,
    start_date="2023-01-01",
    end_date="2023-12-31",
    keywords=["关键词1", "关键词2"],
    limit=100
)
```

## 注意事项

1. **请求间隔**: 建议将请求间隔设置为适当的值（默认10秒），避免被微信公众平台限制访问。
2. **登录缓存**: 登录信息会缓存到本地文件，有效期有限，期间可重复使用而无需重新登录。
3. **数据库存储**: 建议启用数据库存储，便于后续查询和分析。
4. **多线程限制**: 过多的线程可能导致账号被限制，建议将`threads`控制在3-5之间。
5. **数据库选择**: 
   - 对于小型项目，SQLite足够使用
   - 对于大型项目，推荐使用MySQL等关系型数据库
   - 需要使用MySQL时，请先安装pymysql: `pip install pymysql`

## 依赖项

- Python 3.6+
- requests
- selenium
- beautifulsoup4
- tqdm
- markdownify
- pandas
- numpy
- loguru
- webdriver-manager
- lxml
- schedule (用于定时爬虫功能)

详见 `requirements.txt`。

## 未来规划

项目计划在后续版本中添加以下功能：

1. **微博内容爬虫**: 支持爬取微博用户、话题和搜索结果
2. **知乎内容爬虫**: 支持爬取知乎专栏、问答和用户文章
3. **内容分析功能**: 提供基础的文本分析和数据可视化功能
4. **异步爬虫**: 使用asyncio提高爬取效率
5. **代理支持**: 添加代理IP池，提高稳定性和规避封禁

欢迎贡献代码或提交Issue！

## 许可证

MIT License 
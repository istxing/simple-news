# Simple News

**简洁的新闻聚合工具** - 基于 TrendRadar 核心功能精简而来

## ✨ 特性

- 📰 **多平台新闻聚合** - 支持今日头条、华尔街见闻、澎湃新闻、36氪等主流平台
- 🔍 **关键词监控** - 自定义关键词，快速发现感兴趣的新闻
- 💾 **本地存储** - SQLite 数据库，轻量高效
- 📊 **美观报告** - 自动生成响应式 HTML 报告
- 📲 **Bark 推送** - 向 iOS 设备推送通知
- ⚙️ **简单配置** - YAML 配置文件，易于定制

## 🚀 快速开始

### 1. 安装依赖

```bash
cd simple_news
pip install -r requirements.txt
```

### 2. 编辑配置

编辑 `config/config.yaml` 和 `config/keywords.txt` 文件，配置监控的平台和关键词。

### 3. 运行

```bash
# 方式 1: 使用模块运行
python -m simple_news

# 方式 2: 使用启动脚本
python run.py
```

### 4. 查看报告

运行完成后，在 `output/reports/` 目录查看生成的 HTML 报告：

```bash
# 打开报告
open output/reports/index.html
```

## 🚀 部署

查看 [DEPLOY.md](DEPLOY.md) 获取 Debian/Ubuntu 服务器部署指南（含 Systemd 定时任务配置）。

## 📁 项目结构

```
simple_news/
├── simple_news/          # 核心代码
│   ├── __init__.py
│   ├── __main__.py       # 主程序入口
│   ├── config.py         # 配置管理
│   ├── crawler.py        # 新闻爬虫
│   ├── storage.py        # 数据存储
│   ├── analyzer.py       # 关键词分析
│   ├── reporter.py       # HTML 报告生成
│   └── notifier.py       # Bark 推送通知
├── config/               # 配置文件
│   ├── config.yaml       # 主配置
│   └── keywords.txt      # 关键词列表
├── output/               # 输出目录
│   ├── news_YYYYMMDD.db  # 按日期分库的 SQLite 数据库
│   └── reports/          # HTML 报告（仅 index.html）
├── requirements.txt      # 依赖列表
├── run.py               # 快速启动脚本
└── README.md            # 本文件
```

## ⚙️ 配置说明

### config.yaml

```yaml
# 应用设置
app:
  timezone: "Asia/Shanghai"  # 时区

# 平台配置
platforms:
  - id: "zhihu"
    name: "知乎"
  - id: "weibo"
    name: "微博"
  # ... 更多平台

# 爬虫设置
crawler:
  request_interval: 2000  # 请求间隔（毫秒）
  use_proxy: false        # 是否使用代理

# 存储设置
storage:
  data_dir: "output"      # 数据目录
  retention_days: 7       # 数据保留天数
  push_window:            # 推送时间窗口（静默时间控制）
    enabled: true
    start: "08:00"        # 开始推送时间
    end: "23:00"          # 结束推送时间

# 报告设置
report:
  mode: "incremental"     # current | daily | incremental
  rank_threshold: 5       # 排名高亮阈值
  max_news_per_keyword: 0 # 每个关键词最大显示条数（0=不限制）

# 通知设置
notification:
  bark:
    enabled: true
    url: ""               # Bark 推送 URL
```

### 通知配置（Bark）

Bark 是一款支持自定义推送的 iOS App，可将新闻推送到你的 iPhone。

**配置步骤：**

1. 在 App Store 下载安装 [Bark](https://apps.apple.com/cn/app/bark/id1403753865)
2. 打开 App，复制推送 URL（格式：`https://api.day.app/YOUR_KEY/`）
3. 在 `config/config.yaml` 中启用并配置：

```yaml
notification:
  enabled: true
  bark_url: "https://api.day.app/YOUR_KEY/"
```


### keywords.txt

每行一个关键词，支持 `#` 开头的注释：

```
# 科技类
AI
人工智能
ChatGPT

# 财经类
股市
经济
```

## 📊 报告模式

- **current** - 当前榜单模式（只显示最新一批爬取的新闻）
- **daily** - 全天汇总模式（显示当天所有爬取的新闻）
- **incremental** - 增量模式（过滤今天+昨天已出现的新闻，只返回真正新增的）

## 🔧 命令行选项

```bash
# 显示版本
python -m simple_news --version

# 使用自定义配置文件
python -m simple_news --config custom.yaml

# 显示帮助
python -m simple_news --help
```

## 🤝 致谢

本项目基于 [TrendRadar](https://github.com/sansan0/TrendRadar) 的核心功能精简而来，感谢原作者。

## 📝 许可证

MIT License

---

**Simple News** - 让新闻聚合更简单 ✨

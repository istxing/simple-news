# Simple News 部署指南 (Debian/Ubuntu)

本指南将帮助你在 Debian 或 Ubuntu 服务器上部署 Simple News 项目，并配置自动定时运行。

## 1. 环境准备

首先确保服务器已安装 Python 3.8+ 和 git。

```bash
# 更新系统包
sudo apt update
sudo apt upgrade -y

# 安装 Python 和相关工具
sudo apt install -y python3 python3-pip python3-venv git
```

## 2. 获取代码

将代码克隆到服务器上的用户目录。

```bash
# 示例：部署到 ~/simple_news
cd ~
git clone <你的仓库地址> simple_news
cd simple_news

# 如果是上传 zip 包：
# unzip simple_news.zip -d ~/simple_news
# cd ~/simple_news
```

## 3. 安装依赖

创建 Python 虚拟环境并安装依赖，避免污染系统环境。

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境并安装依赖
./venv/bin/pip install -r requirements.txt
```

## 4. 配置文件

复制示例配置并根据需要修改。

```bash
# 创建配置目录（如果不存在）
mkdir -p config

# ⚠️ 重要：配置环境变量（推荐）
# 复制示例文件并填入敏感信息（如 Bark URL）
cp .env.example .env
nano .env

# ⚠️ 同时也需要上传或创建 config.yaml 和 keywords.txt
# 可以直接在服务器上编辑：
nano config/config.yaml
nano config/keywords.txt
```

确保 `config.yaml` 中的路径配置正确：

```yaml
storage:
  data_dir: "output"  # 相对路径即可
```

## 5. 运行测试

在配置定时任务前，先手动运行一次确保一切正常。

```bash
# 使用虚拟环境的 Python 运行
./venv/bin/python -m simple_news
```

如果看到类似 `✅ 完成！` 的输出，说明运行成功。

## 6. 设置定时任务 (Systemd)

推荐使用 Systemd Timer 来管理定时任务。项目 `systemd/` 目录下已提供模板文件。

### 6.1 配置 Service 文件

编辑 `systemd/simple-news.service`，**务必修改 `User`、`WorkingDirectory` 和 `ExecStart` 为实际值**。

```bash
nano systemd/simple-news.service
```

修改示例（假设用户名为 `ubuntu`）：
```ini
[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/simple_news
ExecStart=/home/ubuntu/simple_news/venv/bin/python -m simple_news
```

### 6.2 配置 Timer 文件

编辑 `systemd/simple-news.timer` 修改运行频率（默认每小时的第 54 分钟运行一次）。

```bash
nano systemd/simple-news.timer
```

### 6.3 安装并启动服务

```bash
# 复制文件到 systemd 目录
sudo cp systemd/simple-news.service /etc/systemd/system/
sudo cp systemd/simple-news.timer /etc/systemd/system/

# 重载配置
sudo systemctl daemon-reload

# 启用并启动 Timer
sudo systemctl enable --now simple-news.timer

# 查看 Timer 状态
systemctl list-timers --all | grep simple-news
```

### 6.4 查看日志

运行日志将输出到 `/var/log/simple_news.log` (如果按模板配置) 或通过 `journalctl` 查看：

```bash
# 查看服务日志
sudo journalctl -u simple-news.service -f
```

## 7. 其他说明

- **更新代码**：
  ```bash
  cd ~/simple_news
  
  # 1. 拉取更新代码
  git pull
  
  # 2. 如果有依赖变更
  ./venv/bin/pip install -r requirements.txt
  
  # 3. 检查是否有新配置项
  # 建议对比 .env.example 和你的 .env，补充新的配置项
  # 推荐使用 .env 管理所有自定义配置以避免 git 冲突
  ```

- **查看报告**：
  报告生成在 `output/reports/index.html`。你可以使用 `python -m http.server` 临时查看，或配置 Nginx 托管该目录。

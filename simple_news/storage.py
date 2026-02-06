# coding=utf-8
"""
存储模块
负责将新闻数据保存到 SQLite 数据库
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import pytz


class NewsStorage:
    """新闻存储类"""

    def __init__(self, config: Dict):
        """
        初始化存储
        
        Args:
            config: 配置字典
        """
        self.config = config
        storage_config = config['storage']
        
        # 数据目录
        self.data_dir = Path(storage_config['data_dir'])
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 时区
        self.timezone = pytz.timezone(config['app']['timezone'])
        
        # 保留天数
        self.retention_days = storage_config.get('retention_days', 30)
        
        # 迁移旧数据库（如果存在）
        self._migrate_from_single_db()
    
    def _get_db_path(self, date: Optional[str] = None) -> Path:
        """
        获取指定日期的数据库路径
        
        Args:
            date: 日期字符串 (YYYY-MM-DD)，默认为今天
        
        Returns:
            数据库文件路径
        """
        if date is None:
            date = datetime.now(self.timezone).strftime('%Y-%m-%d')
        
        # 格式化为 YYYYMMDD
        date_str = date.replace('-', '')
        db_filename = f'news_{date_str}.db'
        
        return self.data_dir / db_filename

    def _init_database_for_path(self, db_path: Path):
        """
        为指定路径初始化数据库表
        
        Args:
            db_path: 数据库文件路径
        """
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 新闻表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform_id TEXT NOT NULL,
                    platform_name TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT,
                    mobile_url TEXT,
                    rank INTEGER,
                    crawl_time TEXT NOT NULL,
                    date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            ''')
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_news_date 
                ON news(date)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_news_platform 
                ON news(platform_id, date)
            ''')
            
            # 关键词统计表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS keyword_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL,
                    count INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_keyword_date 
                ON keyword_stats(date)
            ''')
            
            conn.commit()
    
    def _migrate_from_single_db(self):
        """
        从单一数据库迁移到按日期分库
        将 news.db 中的数据按日期拆分到独立数据库
        """
        old_db = self.data_dir / 'news.db'
        
        if not old_db.exists():
            return
        
        print("🔄 检测到旧数据库，开始迁移...")
        
        try:
            # 读取所有数据
            with sqlite3.connect(old_db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM news")
                rows = cursor.fetchall()
            
            if not rows:
                print("  旧数据库为空，跳过迁移")
                return
            
            # 按日期分组
            from collections import defaultdict
            by_date = defaultdict(list)
            
            for row in rows:
                date = row[8]  # date 字段索引
                by_date[date].append(row)
            
            # 写入各日期数据库
            migrated_count = 0
            for date, news_list in by_date.items():
                db_path = self._get_db_path(date)
                self._init_database_for_path(db_path)
                
                with sqlite3.connect(db_path) as conn:
                    conn.executemany(
                        '''INSERT INTO news (
                            id, platform_id, platform_name, title, url, mobile_url,
                            rank, crawl_time, date, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        news_list
                    )
                    migrated_count += len(news_list)
                
                print(f"  ✓ {date}: {len(news_list)} 条新闻")
            
            # 备份并删除旧数据库
            backup_path = self.data_dir / 'news.db.backup'
            old_db.rename(backup_path)
            print(f"✓ 迁移完成！共迁移 {migrated_count} 条新闻")
            print(f"  旧数据库已备份为: {backup_path.name}")
            
        except Exception as e:
            print(f"✗ 迁移失败: {str(e)}")
            print("  将继续使用旧数据库格式")

    def save_news(self, platform_data_list: List[Dict]) -> int:
        """
        保存新闻数据
        
        Args:
            platform_data_list: 平台数据列表
            
        Returns:
            保存的新闻条数
        """
        now = datetime.now(self.timezone)
        crawl_time = now.strftime('%Y-%m-%d %H:%M:%S')
        date = now.strftime('%Y-%m-%d')
        
        # 获取当天数据库路径
        db_path = self._get_db_path(date)
        
        # 初始化数据库（如果不存在）
        self._init_database_for_path(db_path)
        
        total_saved = 0
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            for platform_data in platform_data_list:
                platform_id = platform_data['platform_id']
                platform_name = platform_data['platform_name']
                
                for news_item in platform_data['news_list']:
                    cursor.execute('''
                        INSERT INTO news (
                            platform_id, platform_name, title, url, mobile_url,
                            rank, crawl_time, date, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        platform_id,
                        platform_name,
                        news_item['title'],
                        news_item['url'],
                        news_item['mobile_url'],
                        news_item['rank'],
                        crawl_time,
                        date,
                        crawl_time,
                    ))
                    total_saved += 1
            
            conn.commit()
        
        print(f"✓ 已保存 {total_saved} 条新闻到数据库")
        
        # 清理旧数据
        if self.retention_days > 0:
            self._cleanup_old_data()
        
        return total_saved

    def save_keyword_stats(self, keyword_stats: Dict[str, int]):
        """
        保存关键词统计
        
        Args:
            keyword_stats: {关键词: 出现次数} 字典
        """
        if not keyword_stats:
            return
        
        now = datetime.now(self.timezone)
        created_at = now.strftime('%Y-%m-%d %H:%M:%S')
        date = now.strftime('%Y-%m-%d')
        
        # 获取当天数据库路径
        db_path = self._get_db_path(date)
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            for keyword, count in keyword_stats.items():
                cursor.execute('''
                    INSERT INTO keyword_stats (keyword, count, date, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (keyword, count, date, created_at))
            
            conn.commit()

    def get_today_news(self, mode: str = 'daily') -> List[Dict]:
        """
        获取今天的新闻
        
        Args:
            mode: 查询模式
                - daily: 全天汇总（今天所有爬取的新闻）
                - current: 当前榜单（最新一次爬取的新闻）
                - incremental: 增量更新（过滤今天+昨天已有的，返回真正新增的新闻）
        
        Returns:
            新闻列表
        """
        today = datetime.now(self.timezone).strftime('%Y-%m-%d')
        db_path = self._get_db_path(today)
        
        # 如果数据库不存在，返回空列表
        if not db_path.exists():
            return []
        
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if mode == 'current':
                # 获取最新一批爬取的新闻
                cursor.execute('''
                    SELECT * FROM news 
                    WHERE date = ? 
                    AND crawl_time = (
                        SELECT MAX(crawl_time) FROM news WHERE date = ?
                    )
                    ORDER BY platform_id, rank
                ''', (today, today))
            elif mode == 'incremental':
                # 增量模式：对比今天已保存的所有新闻（最新一批之前的），返回新增的新闻
                # 获取最新一批的爬取时间
                cursor.execute('''
                    SELECT MAX(crawl_time) as latest_time FROM news WHERE date = ?
                ''', (today,))
                result = cursor.fetchone()
                latest_time = result['latest_time'] if result else None
                
                if not latest_time:
                    return []
                
                # 获取今天这批之前的所有标题（不包括最新一批）
                cursor.execute('''
                    SELECT DISTINCT title FROM news 
                    WHERE date = ? AND crawl_time < ?
                ''', (today, latest_time))
                existing_titles = {row['title'] for row in cursor.fetchall()}
                
                # 也检查昨天的数据库
                yesterday = (datetime.now(self.timezone) - timedelta(days=1)).strftime('%Y-%m-%d')
                yesterday_db = self._get_db_path(yesterday)
                if yesterday_db.exists():
                    with sqlite3.connect(yesterday_db) as yesterday_conn:
                        yesterday_conn.row_factory = sqlite3.Row
                        yesterday_cursor = yesterday_conn.cursor()
                        yesterday_cursor.execute('SELECT DISTINCT title FROM news')
                        existing_titles.update({row['title'] for row in yesterday_cursor.fetchall()})
                
                # 获取最新一批的新闻
                cursor.execute('''
                    SELECT * FROM news 
                    WHERE date = ? AND crawl_time = ?
                    ORDER BY platform_id, rank
                ''', (today, latest_time))
                latest_news = [dict(row) for row in cursor.fetchall()]
                
                # 过滤出新增的新闻（标题不在之前的记录中）
                incremental_news = [
                    news for news in latest_news 
                    if news['title'] not in existing_titles
                ]
                return incremental_news
            else:  # daily
                # 获取全天的新闻
                cursor.execute('''
                    SELECT * FROM news 
                    WHERE date = ?
                    ORDER BY created_at DESC, platform_id, rank
                ''', (today,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def _cleanup_old_data(self):
        """清理过期数据（删除旧的数据库文件）"""
        if self.retention_days <= 0:
            return
        
        cutoff_date = datetime.now(self.timezone) - timedelta(days=self.retention_days)
        
        # 遍历数据目录中的所有数据库文件
        deleted_count = 0
        for db_file in self.data_dir.glob('news_*.db'):
            # 提取日期
            date_str = db_file.stem.replace('news_', '')  # 20260206
            try:
                file_date = datetime.strptime(date_str, '%Y%m%d')
                
                # 如果文件过期，删除
                if file_date.date() < cutoff_date.date():
                    db_file.unlink()
                    deleted_count += 1
                    print(f"  ✓ 已删除过期数据库: {db_file.name}")
            except ValueError:
                # 跳过格式不正确的文件
                continue
        
        if deleted_count > 0:
            print(f"✓ 清理完成，删除了 {deleted_count} 个过期数据库文件")

    def get_database_stats(self) -> Dict:
        """
        获取数据库统计信息
        
        Returns:
            统计信息字典
        """
        total_news = 0
        platforms = set()
        db_files = list(self.data_dir.glob('news_*.db'))
        
        # 获取今天的日期
        today = datetime.now(self.timezone).strftime('%Y-%m-%d')
        today_news = 0
        
        # 遍历所有数据库文件
        for db_file in db_files:
            with sqlite3.connect(db_file) as conn:
                cursor = conn.cursor()
                
                # 统计新闻数
                cursor.execute("SELECT COUNT(*) FROM news")
                count = cursor.fetchone()[0]
                total_news += count
                
                # 统计今日新闻数
                cursor.execute("SELECT COUNT(*) FROM news WHERE date = ?", (today,))
                today_count = cursor.fetchone()[0]
                today_news += today_count
                
                # 统计平台数
                cursor.execute("SELECT DISTINCT platform_id FROM news")
                platforms.update([row[0] for row in cursor.fetchall()])
        
        # 计算总大小
        total_size = sum(f.stat().st_size for f in db_files) / (1024 * 1024)  # MB
        
        return {
            'total_news': total_news,
            'today_news': today_news,
            'platform_count': len(platforms),
            'database_count': len(db_files),
            'db_size_mb': round(total_size, 2),
            'data_dir': str(self.data_dir),
        }

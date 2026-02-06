# coding=utf-8
"""
HTML 报告生成模块
将新闻数据生成美观的 HTML 报告
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List
import shutil
import pytz


class HTMLReporter:
    """HTML 报告生成器"""

    def __init__(self, config: Dict, report_dir: Path):
        """
        初始化报告生成器
        
        Args:
            config: 配置字典
            report_dir: 报告输出目录
        """
        self.config = config
        self.reports_dir = Path(report_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        self.timezone = pytz.timezone(config['app']['timezone'])
        self.rank_threshold = config['report'].get('rank_threshold', 5)

    def generate(
        self, 
        keyword_data: List[Dict],
        platform_data_list: List[Dict],
        stats: Dict
    ) -> Path:
        """
        生成 HTML 报告
        
        Args:
            keyword_data: 关键词数据列表
            platform_data_list: 平台数据列表
            stats: 统计信息
            
        Returns:
            HTML 文件路径
        """
        now = datetime.now(self.timezone)
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        date_str = now.strftime('%Y%m%d_%H%M%S')
        
        html_content = self._generate_html(
            keyword_data, platform_data_list, stats, timestamp
        )
        
        # 保存报告
        report_path = self.reports_dir / f'report_{date_str}.html'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 同时保存为 index.html（方便访问）
        index_path = self.reports_dir / 'index.html'
        shutil.copy2(report_path, index_path)
        
        return report_path

    def _generate_html(
        self,
        keyword_data: List[Dict],
        platform_data_list: List[Dict],
        stats: Dict,
        timestamp: str
    ) -> str:
        """生成 HTML 内容"""
        
        # 关键词统计部分
        keyword_section = self._generate_keyword_section(keyword_data)
        
        # 平台新闻部分
        platform_section = self._generate_platform_section(platform_data_list)
        
        # 完整 HTML
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simple News 报告 - {timestamp}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .header .subtitle {{
            opacity: 0.9;
            font-size: 1.1em;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            padding: 20px 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }}
        
        .stat-item {{
            text-align: center;
            padding: 10px;
        }}
        
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .stat-label {{
            color: #6c757d;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section-title {{
            font-size: 1.8em;
            font-weight: 700;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
            color: #333;
        }}
        
        .keyword-item {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 4px solid #667eea;
        }}
        
        .keyword-header {{
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .keyword-name {{
            font-size: 1.3em;
            font-weight: 600;
            color: #333;
            margin-right: 10px;
        }}
        
        .keyword-count {{
            background: #667eea;
            color: white;
            padding: 3px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
        }}
        
        .news-item {{
            background: white;
            padding: 12px 15px;
            margin-bottom: 8px;
            border-radius: 6px;
            border-left: 3px solid transparent;
            transition: all 0.3s ease;
        }}
        
        .news-item:hover {{
            border-left-color: #667eea;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
            transform: translateX(5px);
        }}
        
        .news-title {{
            color: #333;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .news-title:hover {{
            color: #667eea;
        }}
        
        .rank {{
            display: inline-block;
            min-width: 30px;
            text-align: center;
            font-weight: 600;
            color: #6c757d;
        }}
        
        .rank.hot {{
            color: #dc3545;
            font-weight: 700;
        }}
        
        .platform {{
            display: inline-block;
            background: #e9ecef;
            color: #495057;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.85em;
        }}
        
        .platform-section {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        
        .platform-header {{
            font-size: 1.3em;
            font-weight: 600;
            margin-bottom: 15px;
            color: #333;
            padding-bottom: 10px;
            border-bottom: 2px solid #dee2e6;
        }}
        
        .footer {{
            padding: 20px 30px;
            background: #f8f9fa;
            text-align: center;
            color: #6c757d;
            border-top: 1px solid #e9ecef;
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
            
            .header h1 {{
                font-size: 1.8em;
            }}
            
            .stats {{
                grid-template-columns: repeat(2, 1fr);
            }}
            
            .content {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 Simple News</h1>
            <div class="subtitle">简洁的新闻聚合报告</div>
            <div class="subtitle">{timestamp}</div>
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-value">{stats.get('total_news', 0)}</div>
                <div class="stat-label">总新闻数</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{stats.get('today_news', 0)}</div>
                <div class="stat-label">今日新闻</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{len(platform_data_list)}</div>
                <div class="stat-label">平台数量</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{len(keyword_data)}</div>
                <div class="stat-label">关键词匹配</div>
            </div>
        </div>
        
        <div class="content">
            {keyword_section}
            {platform_section}
        </div>
        
        <div class="footer">
            <p>Powered by Simple News | 数据库大小: {stats.get('db_size_mb', 0)} MB</p>
        </div>
    </div>
</body>
</html>'''
        
        return html

    def _generate_keyword_section(self, keyword_data: List[Dict]) -> str:
        """生成关键词统计部分"""
        if not keyword_data:
            return '<div class="section"><div class="section-title">🔍 关键词统计</div><p>暂无关键词匹配</p></div>'
        
        items_html = []
        for item in keyword_data:
            group_name = item['group_name']  # 使用组名
            count = item['count']
            news_list = item['news_list']
            
            news_items_html = []
            for news in news_list:
                rank = news.get('rank', 0)
                rank_class = 'hot' if rank <= self.rank_threshold else ''
                platform_name = news.get('platform_name', '未知')
                title = news.get('title', '')
                url = news.get('url', '#')
                
                news_items_html.append(f'''
                <div class="news-item">
                    <a href="{url}" target="_blank" class="news-title">
                        <span class="rank {rank_class}">#{rank}</span>
                        <span class="platform">{platform_name}</span>
                        <span>{title}</span>
                    </a>
                </div>
                ''')
            
            items_html.append(f'''
            <div class="keyword-item">
                <div class="keyword-header">
                    <span class="keyword-name">{group_name}</span>
                    <span class="keyword-count">{count} 条</span>
                </div>
                <div class="keyword-news">
                    {''.join(news_items_html)}
                </div>
            </div>
            ''')
        
        return f'''
        <div class="section">
            <div class="section-title">🔍 关键词统计</div>
            {''.join(items_html)}
        </div>
        '''

    def _generate_platform_section(self, platform_data_list: List[Dict]) -> str:
        """生成平台新闻部分"""
        if not platform_data_list:
            return ''
        
        platforms_html = []
        for platform_data in platform_data_list:
            platform_name = platform_data['platform_name']
            news_list = platform_data['news_list']
            
            news_items_html = []
            for news in news_list:
                rank = news.get('rank', 0)
                rank_class = 'hot' if rank <= self.rank_threshold else ''
                title = news.get('title', '')
                url = news.get('url', '#')
                
                news_items_html.append(f'''
                <div class="news-item">
                    <a href="{url}" target="_blank" class="news-title">
                        <span class="rank {rank_class}">#{rank}</span>
                        <span>{title}</span>
                    </a>
                </div>
                ''')
            
            platforms_html.append(f'''
            <div class="platform-section">
                <div class="platform-header">{platform_name} ({len(news_list)} 条)</div>
                {''.join(news_items_html)}
            </div>
            ''')
        
        return f'''
        <div class="section">
            <div class="section-title">📱 平台新闻</div>
            {''.join(platforms_html)}
        </div>
        '''

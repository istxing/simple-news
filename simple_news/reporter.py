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
        """生成简约 Tab 风格 HTML 内容"""
        
        # 生成 Tab 按钮和内容
        tabs_html = []
        sections_html = []
        tab_index = 0
        
        # 关键词新闻作为第一个 Tab（如果有数据）
        if keyword_data:
            active_class = 'active' if tab_index == 0 else ''
            tabs_html.append(f'<button class="tab-btn {active_class}" onclick="switchTab(\'tab_{tab_index}\')">🔍 关键词新闻</button>')
            
            keyword_items_html = []
            for item in keyword_data:
                group_name = item['group_name']
                count = item['count']
                news_list = item['news_list']
                
                news_items = []
                for news in news_list:
                    rank = news.get('rank', 0)
                    rank_class = 'hot' if rank <= self.rank_threshold else ''
                    platform_name = news.get('platform_name', '未知')
                    title = news.get('title', '')
                    url = news.get('url', '#')
                    news_items.append(f'''
                <div class="news-item">
                    <a href="{url}" target="_blank" class="news-title">
                        <span class="rank {rank_class}">#{rank}</span>
                        <span class="platform">{platform_name}</span>
                        <span>{title}</span>
                    </a>
                </div>''')
                
                keyword_items_html.append(f'''
            <div class="keyword-group">
                <div class="keyword-header">
                    <span class="keyword-name">{group_name}</span>
                    <span class="keyword-count">{count} 条</span>
                </div>
                {''.join(news_items)}
            </div>''')
            
            sections_html.append(f'''
            <div id="tab_{tab_index}" class="platform-section {active_class}">
                <div class="platform-header">关键词新闻 ({sum(item['count'] for item in keyword_data)} 条)</div>
                {''.join(keyword_items_html)}
            </div>''')
            tab_index += 1
        
        # 平台新闻 Tabs
        for platform_data in platform_data_list:
            platform_name = platform_data['platform_name']
            news_list = platform_data['news_list']
            
            active_class = 'active' if tab_index == 0 else ''
            tabs_html.append(f'<button class="tab-btn {active_class}" onclick="switchTab(\'tab_{tab_index}\')">{platform_name}</button>')
            
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
                </div>''')
            
            sections_html.append(f'''
            <div id="tab_{tab_index}" class="platform-section {active_class}">
                <div class="platform-header">{platform_name} ({len(news_list)} 条)</div>
                {''.join(news_items_html)}
            </div>''')
            tab_index += 1
        
        # 计算今日收录总数
        total_today = stats.get('today_news', 0)
        
        # 完整 HTML
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simple News 报告</title>
    <style>
        :root {{
            --primary-color: #2c3e50;
            --accent-color: #3498db;
            --bg-color: #f5f7fa;
            --card-bg: #ffffff;
            --text-color: #333333;
            --text-secondary: #7f8c8d;
            --border-color: #eaeaea;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            padding: 40px 20px;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: var(--card-bg);
            box-shadow: 0 2px 10px rgba(0,0,0,0.03);
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--border-color);
        }}
        
        .header {{
            background: #fff;
            color: var(--primary-color);
            padding: 40px 40px 20px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}
        
        .header h1 {{ font-size: 2em; margin-bottom: 5px; font-weight: 600; }}
        .header .subtitle {{ color: var(--text-secondary); font-size: 1em; }}
        
        .stats {{
            display: flex;
            gap: 40px;
            padding: 20px 40px;
            background: #fff;
            border-bottom: 1px solid var(--border-color);
        }}
        
        .stat-item {{ text-align: left; }}
        .stat-value {{ font-size: 1.8em; font-weight: 700; color: var(--primary-color); }}
        .stat-label {{ color: var(--text-secondary); font-size: 0.85em; text-transform: uppercase; }}
        
        .content {{ padding: 40px; }}
        
        .tabs-header {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 30px;
            padding-bottom: 0;
        }}

        .tab-btn {{
            background: none;
            border: none;
            padding: 10px 5px;
            font-size: 0.95em;
            font-weight: 500;
            color: var(--text-secondary);
            cursor: pointer;
            margin-bottom: -1px;
            transition: color 0.2s;
        }}

        .tab-btn:hover {{ color: var(--primary-color); }}
        .tab-btn.active {{
            color: var(--primary-color);
            font-weight: 600;
            border-bottom: 2px solid var(--primary-color);
        }}

        .platform-section {{ display: none; }}
        .platform-section.active {{ display: block; animation: fadeIn 0.3s ease; }}
        
        .platform-header {{
            font-size: 1.2em;
            font-weight: 600;
            margin-bottom: 15px;
            color: var(--primary-color);
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(5px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .news-item {{
            padding: 10px 0;
            border-bottom: 1px solid #f5f5f5;
        }}
        .news-item:last-child {{ border-bottom: none; }}
        
        .news-title {{
            color: var(--text-color);
            text-decoration: none;
            display: flex;
            align-items: flex-start;
            gap: 12px;
            font-size: 1em;
            line-height: 1.5;
        }}
        .news-title:hover {{ color: var(--accent-color); }}
        
        .rank {{
            min-width: 24px;
            text-align: center;
            font-weight: 500;
            color: #b0b0b0;
            font-size: 0.9em;
        }}
        .rank.hot {{ color: #ff6b6b; font-weight: 600; }}
        
        .platform {{
            display: inline-block;
            background: #e9ecef;
            color: #495057;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            white-space: nowrap;
        }}
        
        .keyword-group {{
            margin-bottom: 25px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
        }}
        .keyword-group:last-child {{ border-bottom: none; margin-bottom: 0; }}
        
        .keyword-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 12px;
        }}
        .keyword-name {{ font-weight: 600; color: var(--primary-color); }}
        .keyword-count {{
            background: var(--accent-color);
            color: white;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 0.8em;
        }}
        
        .footer {{
            padding: 30px;
            text-align: center;
            color: var(--text-secondary);
            font-size: 0.9em;
            border-top: 1px solid var(--border-color);
            background: #fff;
        }}
        
        @media (max-width: 768px) {{
            body {{ padding: 10px; }}
            .header, .stats, .content {{ padding: 20px; }}
            .stats {{ flex-wrap: wrap; gap: 20px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>今日热点追踪</h1>
            <div class="subtitle">Simple News 自动生成报告</div>
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-value">{total_today}</div>
                <div class="stat-label">今日总收录</div>
            </div>
        </div>
        
        <div class="content">
            <div class="tabs-header" id="platformTabs">
                {''.join(tabs_html)}
            </div>

            {''.join(sections_html)}
        </div>
        
        <div class="footer">
            Generated by Simple News Monitor • {timestamp}
        </div>
    </div>

    <script>
        function switchTab(tabId) {{
            document.querySelectorAll('.platform-section').forEach(el => {{
                el.classList.remove('active');
            }});
            document.querySelectorAll('.tab-btn').forEach(el => {{
                el.classList.remove('active');
            }});
            const section = document.getElementById(tabId);
            if (section) {{
                section.classList.add('active');
            }}
            const btn = document.querySelector(`button[onclick="switchTab('${{tabId}}')"]`);
            if (btn) {{
                btn.classList.add('active');
            }}
        }}
    </script>
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

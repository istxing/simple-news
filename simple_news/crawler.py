# coding=utf-8
"""
爬虫模块
从 NewsNow API 抓取新闻数据
改编自 trendradar 的 DataFetcher
"""

import json
import random
import time
from typing import Dict, List, Tuple, Optional, Union

import requests


class NewsCrawler:
    """新闻爬虫类"""

    # NewsNow API 地址
    API_URL = "https://newsnow.busiyi.world/api/s"

    # 默认请求头
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
    }

    def __init__(self, config: Dict):
        """
        初始化爬虫
        
        Args:
            config: 配置字典
        """
        self.config = config
        crawler_config = config['crawler']
        
        self.request_interval = crawler_config['request_interval']
        self.use_proxy = crawler_config['use_proxy']
        self.proxy_url = crawler_config.get('proxy', '') if self.use_proxy else None

    def fetch_platform(self, platform_id: str, platform_name: str) -> Optional[Dict]:
        """
        获取单个平台的数据
        
        Args:
            platform_id: 平台ID
            platform_name: 平台名称
            
        Returns:
            新闻数据字典，失败返回 None
        """
        url = f"{self.API_URL}?id={platform_id}&latest"
        
        proxies = None
        if self.proxy_url:
            proxies = {"http": self.proxy_url, "https": self.proxy_url}
        
        max_retries = 2
        for retry in range(max_retries + 1):
            try:
                response = requests.get(
                    url,
                    proxies=proxies,
                    headers=self.HEADERS,
                    timeout=10,
                )
                response.raise_for_status()
                
                data = response.json()
                status = data.get('status', '未知')
                
                if status not in ['success', 'cache']:
                    raise ValueError(f"API 返回异常状态: {status}")
                
                print(f"✓ {platform_name}: 获取成功 ({len(data.get('items', []))} 条)")
                return self._parse_response(data, platform_id, platform_name)
                
            except Exception as e:
                if retry < max_retries:
                    wait_time = random.uniform(3, 5) + retry * 2
                    print(f"✗ {platform_name}: 失败，{wait_time:.1f}秒后重试... ({e})")
                    time.sleep(wait_time)
                else:
                    print(f"✗ {platform_name}: 获取失败 ({e})")
                    return None
        
        return None

    def _parse_response(self, data: Dict, platform_id: str, platform_name: str) -> Dict:
        """
        解析 API 响应
        
        Args:
            data: API 返回的数据
            platform_id: 平台ID
            platform_name: 平台名称
            
        Returns:
            解析后的新闻字典
        """
        news_list = []
        
        for index, item in enumerate(data.get('items', []), 1):
            title = item.get('title')
            
            # 跳过无效标题
            if not title or isinstance(title, (float, int)) or not str(title).strip():
                continue
            
            title = str(title).strip()
            news_list.append({
                'title': title,
                'url': item.get('url', ''),
                'mobile_url': item.get('mobileUrl', ''),
                'rank': index,
            })
        
        return {
            'platform_id': platform_id,
            'platform_name': platform_name,
            'news_list': news_list,
        }

    def crawl_all(self, platforms: List[Tuple[str, str]]) -> List[Dict]:
        """
        爬取所有平台
        
        Args:
            platforms: (平台ID, 平台名称) 元组列表
            
        Returns:
            平台数据列表
        """
        print(f"\n开始爬取 {len(platforms)} 个平台...")
        print("=" * 50)
        
        results = []
        
        for i, (platform_id, platform_name) in enumerate(platforms):
            data = self.fetch_platform(platform_id, platform_name)
            if data:
                results.append(data)
            
            # 请求间隔（最后一个不需要等待）
            if i < len(platforms) - 1:
                interval = self.request_interval + random.randint(-100, 200)
                interval = max(100, interval)  # 至少 100ms
                time.sleep(interval / 1000)
        
        print("=" * 50)
        print(f"爬取完成: 成功 {len(results)}/{len(platforms)} 个平台\n")
        
        return results

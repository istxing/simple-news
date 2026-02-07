# coding=utf-8
"""
通知发送模块

支持 Bark 推送通知，支持分批次发送和 Markdown 链接
"""

import os
import time
import requests
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class Notifier:
    """Bark 通知管理器"""
    
    def __init__(self, config: Dict):
        """初始化通知器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.bark_config = config.get('notification', {}).get('bark', {})
        self.enabled = self.bark_config.get('enabled', False)
        self.url = self.bark_config.get('url', '')
        # 批次配置
        self.max_batch_size = 3600  # Bark 最大批次大小（字节）
        self.batch_interval = 1.0    # 批次间隔（秒）
        
        if not self.enabled:
            print("⏭ Bark 推送未启用")
        elif not self.url:
            print("⏭ Bark URL 未配置")
    
    def check_push_window(self) -> bool:
        """检查当前时间是否在推送窗口内"""
        # 从 storage 配置中读取（暂时放在那里）
        push_config = self.config.get('storage', {}).get('push_window', {})
        
        if not push_config.get('enabled', False):
            return True
            
        start_str = push_config.get('start', '08:00')
        end_str = push_config.get('end', '23:00')
        
        try:
            now = datetime.now().time()
            start_time = datetime.strptime(start_str, "%H:%M").time()
            end_time = datetime.strptime(end_str, "%H:%M").time()
            
            # 正常窗口: 08:00 - 23:00
            if start_time <= end_time:
                is_in_window = start_time <= now <= end_time
            # 跨日窗口: 22:00 - 08:00
            else:
                is_in_window = now >= start_time or now <= end_time
                
            if not is_in_window:
                print(f"💤 当前时间 {now.strftime('%H:%M')} 不在推送窗口 ({start_str}-{end_str})，跳过推送")
                return False
                
            return True
            
        except Exception as e:
            print(f"⚠️ 推送窗口时间解析失败: {e}，默认允许推送")
            return True

    def send_notification(
        self,
        stats: Dict,
        keyword_count: int,
        keyword_data: List[Dict],
        html_report_path: str = None
    ) -> bool:
        """发送通知
        
        Args:
            stats: 数据库统计信息
            keyword_count: 关键词数量
            keyword_data: 关键词详细数据（包含新闻列表）
            html_report_path: HTML 报告文件路径
            
        Returns:
            bool: 是否发送成功
        """
        # 1. 检查推送窗口
        if not self.check_push_window():
            return False

        if not self.enabled:
            print("⏭ Bark 推送未启用")
            return False
            
        if not self.url:
            print("⏭ Bark URL 未配置")
            return False
        
        print("\n📢 发送 Bark 通知...")
        
        # 生成推送批次
        batches = self._split_into_batches(stats, keyword_data, html_report_path)
        
        # 分批次发送（反向顺序）
        success = self._send_batches(batches)
        
        if success:
            print("✓ Bark 推送成功")
        else:
            print("✗ Bark 推送失败")
        
        return success
    
    def _split_into_batches(self, stats: Dict, keyword_data: List[Dict], html_report_path: Optional[str]) -> List[str]:
        """将通知内容分割成多个批次
        
        Args:
            stats: 数据库统计信息
            keyword_data: 关键词详细数据
            html_report_path: HTML 报告路径
        
        Returns:
            批次列表
        """
        batches = []
        now = datetime.now()
        
        # 构建头部（每个批次都包含）
        base_header = f"""**总新闻数：** {stats.get('today_news', 0)}条
**时间：** {now.strftime('%Y-%m-%d %H:%M')}

---

"""
        
        # 构建底部（每个批次都包含）
        base_footer = f"\n\n> 更新时间：{now.strftime('%Y-%m-%d %H:%M:%S')}"

        
        if not keyword_data:
            content = base_header + "暂无匹配的关键词\n" + base_footer
            batches.append(content)
            return batches
        
        # 当前批次内容
        current_batch = base_header
        current_batch_has_content = False
        
        # 内容限制（防止单条新闻过长）

        
        # 处理所有关键词（不限制数量，通过分批次解决）
        total_keywords = len(keyword_data)
        for i, kw in enumerate(keyword_data, 1):
            group_name = kw['group_name']  # 使用组名
            news_list = kw['news_list']
            
            # 关键词标题（仅保留组名）
            keyword_header = f"**{group_name}**\n\n"
            
            # 处理新闻列表
            news_content = ""
            for j, news in enumerate(news_list, 1):
                formatted_news = self._format_news_item(news, j)
                news_content += formatted_news
            
            # 关键词完整内容
            keyword_full_content = keyword_header + news_content
            
            # 关键词间分隔符
            if i < total_keywords:
                keyword_full_content += "---\n\n"
            
            # 检查是否需要分批
            test_content = current_batch + keyword_full_content
            content_size = len(test_content.encode('utf-8')) + len(base_footer.encode('utf-8'))
            
            if content_size >= self.max_batch_size:
                # 当前批次已满，保存并开启新批次
                if current_batch_has_content:
                    batches.append(current_batch + base_footer)
                current_batch = base_header + keyword_full_content
                current_batch_has_content = True
            else:
                # 添加到当前批次
                current_batch = test_content
                current_batch_has_content = True
        
        # 保存最后一个批次
        if current_batch_has_content:
            batches.append(current_batch + base_footer)
        
        return batches
    
    def _format_news_item(self, news: Dict, index: int) -> str:
        """格式化单条新闻（带 Markdown 链接）
        
        Args:
            news: 新闻数据
            index: 序号
        
        Returns:
            格式化的新闻字符串
        """
        title = news.get('title', '')
        url = news.get('url', '')
        platform_name = news.get('platform_name', '')
        rank = news.get('rank', 0)
        
        # 缩短标题（最多80字符）
        if len(title) > 80:
            title = title[:77] + "..."
        
        # 使用 Markdown 链接格式（与 TrendRadar 一致）
        if url:
            formatted_title = f"[{title}]({url})"
        else:
            formatted_title = title
        
        # 格式：序号. [标题](链接)
        #      来源
        result = f"  {index}. {formatted_title}\n"
        # 去掉 [] 和 #排名
        result += f"     `{platform_name}`\n\n"
        
        return result
    
    def _send_batches(self, batches: List[str]) -> bool:
        """批次发送（反向顺序）
        
        Args:
            batches: 批次列表
        
        Returns:
            是否全部成功
        """
        if not batches:
            return False
        
        total_batches = len(batches)
        
        # 反向发送（最后一批先推送，确保客户端显示顺序正确）
        reversed_batches = list(reversed(batches))
        
        if total_batches > 1:
            print(f"将按反向顺序推送 {total_batches} 个批次（最后批次先推送）")
        
        success_count = 0
        for idx, batch_content in enumerate(reversed_batches, 1):
            # 计算用户视角的批次编号
            actual_batch_num = total_batches - idx + 1
            
            content_size = len(batch_content.encode('utf-8'))
            if total_batches > 1:
                print(f"  发送第 {actual_batch_num}/{total_batches} 批次（推送顺序: {idx}/{total_batches}），大小：{content_size} 字节")
            
            # 检查大小警告
            if content_size > 4096:
                print(f"  ⚠️  第 {actual_batch_num} 批次消息过大（{content_size} 字节），可能被拒绝")
            
            # 发送批次
            success = self._send_to_bark_markdown(
                title=f"Simple News [{actual_batch_num}/{total_batches}]" if total_batches > 1 else "Simple News",
                body=batch_content
            )
            
            if success:
                success_count += 1
                if total_batches > 1:
                    print(f"  ✓ 第 {actual_batch_num}/{total_batches} 批次发送成功")
                # 批次间间隔
                if idx < total_batches:
                    time.sleep(self.batch_interval)
            else:
                print(f"  ✗ 第 {actual_batch_num}/{total_batches} 批次发送失败")
        
        return success_count == total_batches
    
    def _send_to_bark_markdown(self, title: str, body: str) -> bool:
        """发送到 Bark（使用 Markdown 格式）
        
        Args:
            title: 通知标题
            body: 通知正文（Markdown）
        
        Returns:
            发送是否成功
        """
        try:
            # 使用 POST 方式发送（支持 Markdown）
            url = self.url.rstrip('/')
            
            # Bark Markdown 推送 payload
            payload = {
                "title": title,
                "markdown": body,  # 使用 markdown 字段
                "sound": "default",
                "group": "SimpleNews"
            }
            
            response = requests.post(
                url,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    return True
                else:
                    print(f"Bark 返回错误: {result.get('message', '未知错误')}")
                    return False
            else:
                print(f"Bark 推送失败: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            print("Bark 推送超时")
            return False
        except requests.exceptions.RequestException as e:
            print(f"Bark 推送异常: {str(e)}")
            return False
        except Exception as e:
            print(f"Bark 推送失败: {str(e)}")
            return False

# coding=utf-8
"""
关键词分析模块
支持关键词分组统计
"""

from typing import Dict, List


class KeywordGroup:
    """关键词组"""
    
    def __init__(self, name: str, keywords: List[str]):
        """
        初始化关键词组
        
        Args:
            name: 组名（显示名称）
            keywords: 组内关键词列表
        """
        self.name = name
        self.keywords = keywords
    
    def matches(self, title: str) -> bool:
        """
        检查标题是否匹配组内任一关键词
        
        Args:
            title: 新闻标题
            
        Returns:
            是否匹配
        """
        return any(kw in title for kw in self.keywords)


class KeywordAnalyzer:
    """关键词分析器"""

    def __init__(self, keyword_groups: List[KeywordGroup]):
        """
        初始化分析器
        
        Args:
            keyword_groups: 关键词组列表
        """
        self.keyword_groups = keyword_groups

    def analyze(self, news_list: List[Dict]) -> Dict[str, List[Dict]]:
        """
        分析新闻中的关键词分组
        
        Args:
            news_list: 新闻列表，每个元素包含 title 等字段
            
        Returns:
            {组名: [匹配的新闻列表]} 字典
        """
        group_news = {}
        
        for group in self.keyword_groups:
            matched_news = []
            seen_titles = set()  # 去重：同一新闻在同组内只计一次
            
            for news in news_list:
                title = news.get('title', '')
                
                # 检查是否匹配且未重复
                if group.matches(title) and title not in seen_titles:
                    matched_news.append(news)
                    seen_titles.add(title)
            
            # 只保留有匹配的组
            if matched_news:
                group_news[group.name] = matched_news
        
        return group_news

    def get_stats(self, group_news: Dict[str, List[Dict]]) -> Dict[str, int]:
        """
        获取关键词组统计
        
        Args:
            group_news: 组名新闻字典
            
        Returns:
            {组名: 出现次数} 字典
        """
        return {group_name: len(news_list) for group_name, news_list in group_news.items()}

    def format_for_display(
        self, 
        group_news: Dict[str, List[Dict]], 
        max_per_group: int = 0,
        weights: Dict[str, float] = None
    ) -> List[Dict]:
        """
        格式化为展示用的数据结构，并根据权重重新排序新闻
        
        Args:
            group_news: 组名新闻字典
            max_per_group: 每个组最多显示的新闻数（0=不限制）
            weights: 排序权重配置 {'rank': 0.6, 'frequency': 0.3, 'hotness': 0.1}
            
        Returns:
            格式化后的列表，按匹配数量降序排列
        """
        result = []
        
        for group_name, news_list in group_news.items():
            # 如果启用了权重排序，重新排序新闻列表
            if weights:
                news_list = self._sort_by_weight(news_list, weights)
            
            # 限制条数
            if max_per_group > 0:
                news_list = news_list[:max_per_group]
            
            # 查找对应的 KeywordGroup 对象
            group_obj = next((g for g in self.keyword_groups if g.name == group_name), None)
            keywords = group_obj.keywords if group_obj else []
            
            result.append({
                'group_name': group_name,      # 组名（显示）
                'keywords': keywords,          # 组内关键词列表
                'count': len(news_list),       # 匹配数量
                'news_list': news_list,        # 新闻列表
            })
        
        # 按匹配数量降序排列
        result.sort(key=lambda x: x['count'], reverse=True)
        
        return result
    
    def _sort_by_weight(
        self, 
        news_list: List[Dict], 
        weights: Dict[str, float]
    ) -> List[Dict]:
        """
        根据权重重新排序新闻
        
        Args:
            news_list: 新闻列表
            weights: 权重配置 {'rank': 0.6, 'frequency': 0.3, 'hotness': 0.1}
            
        Returns:
            排序后的新闻列表
        """
        rank_weight = weights.get('rank', 0.6)
        frequency_weight = weights.get('frequency', 0.3)
        hotness_weight = weights.get('hotness', 0.1)
        
        # 计算每条新闻的综合分数
        for news in news_list:
            rank = news.get('rank', 999)  # 排名，越小越好
            # 将排名转换为分数（排名1 = 100分，排名100 = 1分）
            rank_score = max(0, 101 - rank)
            
            # 热度分数（如果有hotness字段）
            hotness = news.get('hotness', 0)
            hotness_score = hotness / 1000 if hotness else 0  # 归一化
            
            # 频次分数（暂时设为0，因为单条新闻没有频次概念）
            # 如果需要可以统计该新闻在多个平台出现的次数
            frequency_score = 0
            
            # 综合分数
            news['weight_score'] = (
                rank_score * rank_weight +
                frequency_score * frequency_weight +
                hotness_score * hotness_weight
            )
        
        # 按综合分数降序排序
        news_list.sort(key=lambda x: x.get('weight_score', 0), reverse=True)
        
        return news_list

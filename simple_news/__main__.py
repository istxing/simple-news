# coding=utf-8
"""
Simple News 主程序
整合所有模块，执行新闻爬取和报告生成
"""

import argparse
import sys
from pathlib import Path

from simple_news import __version__
from simple_news.config import load_config, load_keywords, get_platform_list
from simple_news.crawler import NewsCrawler
from simple_news.storage import NewsStorage
from simple_news.analyzer import KeywordAnalyzer
from simple_news.reporter import HTMLReporter
from simple_news.notifier import Notifier


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='Simple News - 简洁的新闻聚合工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python -m simple_news                    # 运行一次爬取
  python -m simple_news --config my.yaml  # 使用自定义配置
  python -m simple_news --version          # 显示版本
        '''
    )
    
    parser.add_argument(
        '--config',
        help='配置文件路径',
        default=None
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'Simple News v{__version__}'
    )
    
    args = parser.parse_args()
    
    try:
        # 加载配置
        print(f"\n{'='*60}")
        print(f"Simple News v{__version__}")
        print(f"{'='*60}\n")
        
        print("📋 加载配置...")
        config = load_config(args.config)
        print(f"✓ 配置加载成功")
        
        # 加载关键词
        keywords = load_keywords()
        print(f"✓ 加载了 {len(keywords)} 个词组")
        
        # 获取平台列表
        platforms = get_platform_list(config)
        print(f"✓ 配置了 {len(platforms)} 个平台\n")
        
        # 初始化模块
        crawler = NewsCrawler(config)
        storage = NewsStorage(config)
        analyzer = KeywordAnalyzer(keywords)
        # 确定报告目录
        if config.get('report', {}).get('dir'):
            report_dir = Path(config['report']['dir'])
        else:
            report_dir = Path(config['storage']['data_dir']) / 'reports'
            
        reporter = HTMLReporter(config, report_dir)
        
        # 爬取新闻
        platform_data_list = crawler.crawl_all(platforms)
        
        if not platform_data_list:
            print("\n⚠️  没有成功爬取到任何数据")
            return 1
        
        # 保存到数据库
        print("\n💾 保存数据...")
        storage.save_news(platform_data_list)
        
        # 获取今日新闻用于分析
        mode = config['report']['mode']
        print(f"\n🔍 分析新闻（模式: {mode}）...")
        news_list = storage.get_today_news(mode)
        print(f"✓ 获取了 {len(news_list)} 条新闻用于分析")
        
        # 关键词分析
        keyword_news = analyzer.analyze(news_list)
        keyword_stats = analyzer.get_stats(keyword_news)
        
        # 保存关键词统计
        storage.save_keyword_stats(keyword_stats)
        
        max_per_keyword = config['report'].get('max_news_per_keyword', 0)
        weights = config.get('weight')  # 获取权重配置
        keyword_data = analyzer.format_for_display(keyword_news, max_per_keyword, weights)
        
        print(f"✓ 匹配到 {len(keyword_data)} 个词组")
        
        # 生成 HTML 报告
        print("\n📊 生成报告...")
        stats = storage.get_database_stats()
        report_path = reporter.generate(keyword_data, platform_data_list, stats)
        
        print(f"✓ 报告已生成: {report_path}")
        print(f"✓ 最新报告: {report_path.parent / 'index.html'}")
        
        # 发送通知
        notifier = Notifier(config)
        notifier.send_notification(
            stats=stats,
            keyword_count=len(keyword_data),
            keyword_data=keyword_data,
            html_report_path=str(report_path)
        )
        
        # 显示统计信息
        print("============================================================")
        print("📈 数据库统计")
        print("============================================================")
        print(f"  总新闻数: {stats['total_news']}")
        print(f"  今日新闻: {stats['today_news']}")
        print(f"  平台数量: {stats['platform_count']}")
        print(f"  数据库文件数: {stats.get('database_count', 1)}")
        print(f"  数据库大小: {stats['db_size_mb']} MB")
        print(f"  数据目录: {stats.get('data_dir', 'output')}")
        print(f"{'='*60}\n")
        
        print("✅ 完成！")
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        return 130
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

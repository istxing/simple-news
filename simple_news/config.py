# coding=utf-8
"""
配置管理模块
负责加载和解析 YAML 配置文件
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Tuple
import yaml
from dotenv import load_dotenv


def get_project_root() -> Path:
    """获取项目根目录"""
    # 从当前文件位置向上查找
    current_file = Path(__file__).resolve()
    # simple_news/config.py -> simple_news -> project root
    return current_file.parent.parent


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径，默认为项目根目录下的 config/config.yaml
        
    Returns:
        配置字典
    """
    # 1. 加载环境变量 (支持 .env 文件)
    env_path = get_project_root() / ".env"
    load_dotenv(env_path)

    if config_path is None:
        config_path = get_project_root() / "config" / "config.yaml"
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 2. 环境变量覆盖配置
    _override_from_env(config)
    
    # 验证必要的配置项
    _validate_config(config)
    
    # 处理相对路径
    if not Path(config['storage']['data_dir']).is_absolute():
        config['storage']['data_dir'] = str(
            get_project_root() / config['storage']['data_dir']
        )
    
    # 处理报告目录 (如有)
    if config.get('report', {}).get('dir'):
        report_dir = Path(config['report']['dir'])
        if not report_dir.is_absolute():
             config['report']['dir'] = str(get_project_root() / report_dir)
    
    return config


def _override_from_env(config: Dict[str, Any]) -> None:
    """
    从环境变量覆盖配置
    优先级：环境变量 > config.yaml
    """
    # Bark 配置
    bark_url = os.getenv('BARK_URL')
    if bark_url:
        # 确保路径存在
        config.setdefault('notification', {}).setdefault('bark', {})['url'] = bark_url
        
    bark_enabled = os.getenv('BARK_ENABLED')
    if bark_enabled is not None:
        is_enabled = bark_enabled.lower() in ('true', '1', 'yes', 'on')
        config.setdefault('notification', {}).setdefault('bark', {})['enabled'] = is_enabled

    # 推送窗口配置
    # 注意：根据之前的修改，push_window 位于 storage 下（为了兼容性）
    push_window = config.get('storage', {}).get('push_window', {})
    
    push_enabled = os.getenv('PUSH_WINDOW_ENABLED')
    if push_enabled is not None:
        is_enabled = push_enabled.lower() in ('true', '1', 'yes', 'on')
        push_window['enabled'] = is_enabled
        
    push_start = os.getenv('PUSH_WINDOW_START')
    if push_start:
        push_window['start'] = push_start
        
    push_end = os.getenv('PUSH_WINDOW_END')
    if push_end:
        push_window['end'] = push_end
        
    # 如果 storage 下没有 push_window，确保创建它 (虽然 config.yaml 应该已经有了)
    if 'push_window' not in config.get('storage', {}):
        config.setdefault('storage', {})['push_window'] = push_window


def _validate_config(config: Dict[str, Any]) -> None:
    """
    验证配置文件的完整性
    
    Args:
        config: 配置字典
        
    Raises:
        ValueError: 如果配置缺失必要项
    """
    required_keys = ['app', 'platforms', 'crawler', 'storage', 'report']
    
    for key in required_keys:
        if key not in config:
            raise ValueError(f"配置文件缺少必要项: {key}")
    
    # 验证平台列表
    if not config['platforms']:
        raise ValueError("平台列表不能为空")
    
    for platform in config['platforms']:
        if 'id' not in platform or 'name' not in platform:
            raise ValueError(f"平台配置缺少 id 或 name: {platform}")


def load_keywords(keywords_path: str = None):
    """
    加载关键词分组
    
    Args:
        keywords_path: 关键词文件路径，默认为 config/keywords.txt
        
    Returns:
        KeywordGroup 对象列表
    """
    # 导入 KeywordGroup（避免循环导入）
    from simple_news.analyzer import KeywordGroup
    
    if keywords_path is None:
        keywords_path = get_project_root() / "config" / "keywords.txt"
    else:
        keywords_path = Path(keywords_path)
    
    if not keywords_path.exists():
        print(f"警告: 关键词文件不存在: {keywords_path}")
        return []
    
    groups = []
    current_group_name = None
    current_keywords = []
    
    with open(keywords_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # 跳过注释
            if line.startswith('#'):
                continue
            
            # 空行表示分组结束
            if not line:
                if current_keywords:
                    # 保存当前组
                    name = current_group_name or ' / '.join(current_keywords)
                    groups.append(KeywordGroup(name, current_keywords))
                    current_group_name = None
                    current_keywords = []
                continue
            
            # 组名：[组名]
            if line.startswith('[') and line.endswith(']'):
                # 先保存前一个组（如果有）
                if current_keywords:
                    name = current_group_name or ' / '.join(current_keywords)
                    groups.append(KeywordGroup(name, current_keywords))
                
                # 开始新组
                current_group_name = line[1:-1]
                current_keywords = []
            else:
                # 普通关键词
                current_keywords.append(line)
        
        # 保存最后一个组
        if current_keywords:
            name = current_group_name or ' / '.join(current_keywords)
            groups.append(KeywordGroup(name, current_keywords))
    
    return groups


def get_platform_list(config: Dict[str, Any]) -> List[Tuple[str, str]]:
    """
    从配置中获取平台列表
    
    Args:
        config: 配置字典
        
    Returns:
        (平台ID, 平台名称) 元组列表
    """
    return [(p['id'], p['name']) for p in config['platforms']]

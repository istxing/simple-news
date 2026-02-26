# coding=utf-8
"""
标题主题分类器（与 hotnews 规则保持一致）
"""

from typing import Dict, Tuple


DEFAULT_TOPICS = {
    "topics": {
        "ai": {
            "include": [
                "AI",
                "人工智能",
                "大模型",
                "模型",
                "智能体",
                "Agent",
                "ChatGPT",
                "OpenAI",
                "Anthropic",
                "Gemini",
                "Claude",
                "文心",
                "通义",
                "算力",
                "推理",
                "多模态",
                "AIGC",
                "机器学习",
                "深度学习",
            ],
            "exclude": ["优惠", "折扣", "测评", "开箱"],
        },
        "market": {
            "include": ["美股", "港股", "A股", "股价", "市值", "财报", "营收", "利润", "估值", "加息", "降息", "通胀", "GDP"],
            "exclude": [],
        },
        "industry": {
            "include": ["融资", "并购", "收购", "发布", "上线", "开源", "合作", "裁员", "量产", "产能", "芯片", "工厂"],
            "exclude": [],
        },
        "policy": {
            "include": ["政策", "监管", "法案", "国会", "国务院", "工信部", "发改委", "欧盟", "出口管制", "关税", "制裁"],
            "exclude": [],
        },
        "society": {
            "include": ["教育", "医疗", "就业", "民生", "校园", "医院", "老人", "未成年人", "隐私", "伦理", "诈骗", "公益"],
            "exclude": [],
        },
        "other": {"include": [], "exclude": []},
    }
}


def classify_title(title: str, topics_conf: Dict, default_topic: str = "other") -> Tuple[str, float, str]:
    text = (title or "").lower()
    if topics_conf and topics_conf.get("topics"):
        conf = topics_conf
    elif topics_conf:
        # 兼容 simple_news 配置形态：topics_conf 直接是 {ai:..., general:...}
        conf = {"topics": topics_conf}
    else:
        conf = DEFAULT_TOPICS
    topics = conf.get("topics", {})

    # AI 最高优先级：一旦命中直接返回
    ai_rule = topics.get("ai", {})
    ai_include = [k.lower() for k in ai_rule.get("include", []) if k]
    ai_exclude = [k.lower() for k in ai_rule.get("exclude", []) if k]
    if not any(x in text for x in ai_exclude):
        ai_matched = [k for k in ai_include if k in text]
        if ai_matched:
            ai_score = min(1.0, 0.35 + 0.15 * len(ai_matched))
            return "ai", ai_score, f"matched:{','.join(ai_matched[:4])}"

    best = ("unknown", 0.0, "no_match")
    for topic, rule in topics.items():
        if topic == "ai":
            continue
        include = [k.lower() for k in rule.get("include", []) if k]
        exclude = [k.lower() for k in rule.get("exclude", []) if k]

        if any(x in text for x in exclude):
            continue

        matched = [k for k in include if k in text]
        if matched:
            score = min(1.0, 0.35 + 0.15 * len(matched))
            if score > best[1]:
                best = (topic, score, f"matched:{','.join(matched[:4])}")

    if best[0] == "unknown":
        return default_topic, 0.05, "fallback_default"
    return best

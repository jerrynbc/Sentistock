"""
基于词典的情感分析器

逻辑:
1. 分词 (jieba)
2. 匹配词典 (正向/负向)
3. 结合程度副词调整权重
4. 结合否定词反转极性
5. 归一化到 0-1 区间

优势:
- 针对 A 股财经语境优化
- 无需训练模型，轻量快速
- 可解释性强 (知道是哪些词导致的情感)
"""

import jieba
import jieba.analyse
from typing import Dict, List, Tuple
from .finance_lexicon import (
    FINANCE_POSITIVE_WORDS,
    FINANCE_NEGATIVE_WORDS,
    FINANCE_INTENSIFIERS,
    FINANCE_NEGATORS
)


class LexiconSentimentAnalyzer:
    """词典情感分析器"""
    
    def __init__(self):
        self.pos_words = FINANCE_POSITIVE_WORDS
        self.neg_words = FINANCE_NEGATIVE_WORDS
        self.intensifiers = FINANCE_INTENSIFIERS
        self.negators = FINANCE_NEGATORS
        
    def analyze(self, text: str) -> Dict:
        """
        分析文本情感
        
        Returns:
            {
                'score': 0.0 ~ 1.0 (0.5 为中性)
                'label': 'positive' / 'negative' / 'neutral'
                'keywords': List[str] (提取的关键词)
                'evidence': List[Dict] (情感证据：词 + 极性 + 权重)
            }
        """
        if not text:
            return {'score': 0.5, 'label': 'neutral', 'keywords': [], 'evidence': []}
            
        # 分词
        words = jieba.lcut(text)
        
        raw_score = 0.0
        evidence = []
        
        for i, w in enumerate(words):
            weight = 1.0
            
            # 检查程度副词 (前一个词)
            if i > 0 and words[i-1] in self.intensifiers:
                weight = self.intensifiers[words[i-1]]
                
            # 检查否定词 (前一个词)
            is_negated = False
            if i > 0 and words[i-1] in self.negators:
                is_negated = True
                
            # 匹配情感词
            if w in self.pos_words:
                polarity = 1.0 if not is_negated else -1.0
                raw_score += polarity * weight
                evidence.append({
                    'word': w,
                    'polarity': 'positive' if polarity > 0 else 'negative',
                    'weight': weight,
                    'negated': is_negated
                })
            elif w in self.neg_words:
                polarity = -1.0 if not is_negated else 1.0
                raw_score += polarity * weight
                evidence.append({
                    'word': w,
                    'polarity': 'negative' if polarity < 0 else 'positive',
                    'weight': weight,
                    'negated': is_negated
                })
        
        # 归一化到 0-1 (Sigmoid-like mapping)
        # 公式: 0.5 + score / (abs(score) + 2.0)
        # score=0 => 0.5
        # score=+1 => 0.67
        # score=-1 => 0.33
        # score=+5 => 0.93
        normalized_score = 0.5 + raw_score / (abs(raw_score) + 2.0)
        
        # 标签
        if normalized_score > 0.55:
            label = 'positive'
        elif normalized_score < 0.45:
            label = 'negative'
        else:
            label = 'neutral'
            
        # 提取关键词 (TF-IDF)
        keywords = jieba.analyse.extract_tags(text, topK=5)
        
        return {
            'score': round(normalized_score, 4),
            'label': label,
            'raw_score': raw_score,
            'keywords': keywords,
            'evidence': evidence
        }


# 单例模式，避免重复加载词典
_analyzer = None

def get_analyzer() -> LexiconSentimentAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = LexiconSentimentAnalyzer()
    return _analyzer


def analyze_sentiment(text: str) -> Dict:
    """便捷函数：直接调用分析"""
    return get_analyzer().analyze(text)


if __name__ == "__main__":
    # 测试
    analyzer = get_analyzer()
    
    test_cases = [
        "一季度亏损 6450 万元",  # 应负面
        "已回购 74 万股 金额 8008 万元",  # 应正面
        "一季度营收同比增 28.9%，亏损减至 6450 万元",  # 混合
        "涨停！主力大幅抢筹",  # 强正面
        "跌停，巨量抛售",  # 强负面
    ]
    
    for text in test_cases:
        res = analyzer.analyze(text)
        print(f"文本：{text}")
        print(f"分数：{res['score']:.3f} ({res['label']})")
        print(f"证据：{res['evidence']}")
        print("-" * 40)

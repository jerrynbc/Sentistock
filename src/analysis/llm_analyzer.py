#!/usr/bin/env python3
"""
LLM集成 - GPT-4深度新闻分析
"""

import os
import json
from typing import Dict, List, Optional
from dataclasses import dataclass

# 检查OpenAI库是否可用
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

@dataclass
class NewsAnalysisResult:
    """新闻分析结果"""
    sentiment_score: float  # -1.0 到 1.0，负值表示负面
    confidence: float       # 置信度 0-1
    key_points: List[str]  # 关键要点
    summary: str           # 新闻摘要
    risk_factors: List[str] # 风险因素
    opportunities: List[str] # 机会点
    recommendation: str     # 投资建议

class LLMNewsAnalyzer:
    """LLM新闻分析器"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.client = None
        
        if OPENAI_AVAILABLE and self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
            except Exception as e:
                print(f"⚠️ OpenAI客户端初始化失败: {e}")
                self.client = None
    
    def is_available(self) -> bool:
        """检查LLM是否可用"""
        return self.client is not None
    
    def analyze_news(self, news_text: str, stock_symbol: str = None) -> NewsAnalysisResult:
        """
        使用GPT-4分析新闻内容
        
        Args:
            news_text: 新闻文本
            stock_symbol: 股票代码（可选）
            
        Returns:
            NewsAnalysisResult: 分析结果
        """
        if not self.is_available():
            # 返回基于规则的分析结果
            return self._fallback_analysis(news_text, stock_symbol)
        
        try:
            # 构建分析提示
            prompt = self._build_analysis_prompt(news_text, stock_symbol)
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是一个专业的金融分析师，专注于A股市场。请客观、专业地分析新闻对股票的影响。"},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=1000
            )
            
            # 解析JSON响应
            result_json = json.loads(response.choices[0].message.content)
            return NewsAnalysisResult(**result_json)
            
        except Exception as e:
            print(f"⚠️ LLM分析失败，使用回退方案: {e}")
            return self._fallback_analysis(news_text, stock_symbol)
    
    def _build_analysis_prompt(self, news_text: str, stock_symbol: str = None) -> str:
        """构建分析提示"""
        symbol_info = f"股票代码: {stock_symbol}" if stock_symbol else ""
        
        prompt = f"""
请分析以下财经新闻对A股投资的影响，并以JSON格式返回结果。

{symbol_info}
新闻内容:
{news_text}

请返回包含以下字段的JSON对象：
- sentiment_score: 情感分数 (-1.0 到 1.0，-1.0表示极度负面，1.0表示极度正面)
- confidence: 分析置信度 (0.0 到 1.0)
- key_points: 关键要点列表 (3-5个要点)
- summary: 新闻摘要 (100字以内)
- risk_factors: 风险因素列表 (如果有)
- opportunities: 机会点列表 (如果有)  
- recommendation: 投资建议 ("买入", "卖出", "观望", "谨慎")

确保所有字段都存在，即使某些列表为空。
        """
        return prompt
    
    def _fallback_analysis(self, news_text: str, stock_symbol: str = None) -> NewsAnalysisResult:
        """回退到基于规则的分析"""
        from sentiment.lexicon_analyzer import get_analyzer
        
        try:
            analyzer = get_analyzer()
            result = analyzer.analyze(news_text)
            
            # 基于词典分析计算情感分数
            positive_words = len([e for e in result.get('evidence', []) if e.get('polarity') == 'positive'])
            negative_words = len([e for e in result.get('evidence', []) if e.get('polarity') == 'negative'])
            
            if positive_words + negative_words == 0:
                sentiment_score = 0.0
            else:
                sentiment_score = (positive_words - negative_words) / (positive_words + negative_words)
            
            # 生成回退结果
            key_points = [
                "基于金融词典的情感分析",
                f"正面词汇: {positive_words}个",
                f"负面词汇: {negative_words}个"
            ]
            
            return NewsAnalysisResult(
                sentiment_score=sentiment_score,
                confidence=0.6 if (positive_words + negative_words) > 0 else 0.3,
                key_points=key_points,
                summary="基于规则的情感分析结果",
                risk_factors=["LLM不可用，使用回退方案"] if not self.is_available() else [],
                opportunities=[],
                recommendation="观望" if abs(sentiment_score) < 0.3 else ("买入" if sentiment_score > 0 else "卖出")
            )
            
        except Exception as e:
            # 完全回退
            return NewsAnalysisResult(
                sentiment_score=0.0,
                confidence=0.1,
                key_points=["分析失败，使用默认值"],
                summary="分析失败",
                risk_factors=["分析失败"],
                opportunities=[],
                recommendation="观望"
            )

# 全局实例
llm_analyzer = LLMNewsAnalyzer()
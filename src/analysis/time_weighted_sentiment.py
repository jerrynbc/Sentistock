"""
时间加权情绪分析模块

考虑因素:
1. 时间衰减 - 越旧的消息权重越低
2. 事件影响力 - 重大事件影响更深远
3. 新鲜度 - 新消息权重更高
4. 持续性 - 某些事件影响是持续的
"""

import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class TimeWeightedSentiment:
    """时间加权情绪分析器"""
    
    def __init__(self, half_life_days: float = 7.0):
        """
        初始化
        
        Args:
            half_life_days: 半衰期 (天)，默认 7 天
                           表示 7 天后消息的影响力减半
        """
        self.half_life_days = half_life_days
    
    def calculate_time_weight(self, created_at: str, reference_time: datetime = None) -> float:
        """
        计算时间权重 (指数衰减)
        
        Args:
            created_at: 消息创建时间 (字符串)
            reference_time: 参考时间 (默认当前时间)
        
        Returns:
            时间权重 (0-1 之间)
        
        公式: weight = 0.5 ^ (天数 / 半衰期)
        
        示例:
            - 当天: weight = 1.0
            - 7 天后 (半衰期): weight = 0.5
            - 14 天后: weight = 0.25
            - 30 天后: weight = 0.05
        """
        if reference_time is None:
            reference_time = datetime.now()
        
        # 解析时间
        try:
            event_time = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            event_time = datetime.strptime(created_at[:10], '%Y-%m-%d')
        
        # 计算天数差
        days_diff = (reference_time - event_time).total_seconds() / 86400
        
        # 负数表示未来时间，按 0 天处理
        days_diff = max(0, days_diff)
        
        # 指数衰减
        weight = math.pow(0.5, days_diff / self.half_life_days)
        
        return round(weight, 4)
    
    def calculate_event_impact_weight(self, 
                                     content: str,
                                     reliability: str = 'unknown',
                                     tags: List[str] = None) -> float:
        """
        计算事件影响力权重
        
        Args:
            content: 消息内容
            reliability: 可靠性 ('high', 'medium', 'low', 'unknown')
            tags: 标签列表
        
        Returns:
            影响力权重 (0.5-2.0 之间)
        """
        base_weight = 1.0
        
        # 1. 基于来源可靠性
        reliability_weights = {
            'high': 1.5,      # 高可靠性消息权重更高
            'medium': 1.2,
            'low': 0.8,
            'unknown': 1.0
        }
        base_weight *= reliability_weights.get(reliability, 1.0)
        
        # 2. 基于关键词判断事件重要性
        major_keywords = [
            '裁员', '并购', '重组', '退市', '违法', '调查',
            '重大', '战略', '转型', '突破', '颠覆', '危机',
            '暴涨', '暴跌', '涨停', '跌停'
        ]
        
        moderate_keywords = [
            '业绩', '订单', '合同', '新品', '合作', '协议',
            '高管', '离职', '增持', '减持'
        ]
        
        content_lower = content.lower()
        
        major_count = sum(1 for kw in major_keywords if kw in content_lower)
        moderate_count = sum(1 for kw in moderate_keywords if kw in content_lower)
        
        # 重大事件权重增加
        if major_count > 0:
            base_weight *= (1.0 + major_count * 0.3)  # 每个重大关键词 +30%
        
        if moderate_count > 0:
            base_weight *= (1.0 + moderate_count * 0.15)  # 每个中等关键词 +15%
        
        # 3. 基于标签
        important_tags = ['战略', '财务', '危机', '并购', '政策']
        if tags:
            tag_bonus = sum(0.2 for tag in tags if tag in important_tags)
            base_weight *= (1.0 + tag_bonus)
        
        # 限制权重范围
        base_weight = max(0.5, min(2.0, base_weight))
        
        return round(base_weight, 3)
    
    def calculate_freshness_bonus(self, created_at: str, hours: int = 24) -> float:
        """
        计算新鲜度奖励
        
        Args:
            created_at: 消息创建时间
            hours: 新鲜时间窗口 (小时)
        
        Returns:
            新鲜度奖励 (1.0-1.5 之间)
        """
        try:
            event_time = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            event_time = datetime.strptime(created_at[:10], '%Y-%m-%d')
        
        now = datetime.now()
        hours_diff = (now - event_time).total_seconds() / 3600
        
        if hours_diff <= hours:
            # 24 小时内的消息有额外奖励
            bonus = 1.5 - (hours_diff / hours) * 0.5
            return round(max(1.0, min(1.5, bonus)), 3)
        
        return 1.0
    
    def calculate_weighted_sentiment(self, items: List[Dict]) -> Dict:
        """
        计算加权情绪
        
        Args:
            items: 消息列表，每条消息包含:
                   - content: 内容
                   - created_at: 创建时间
                   - sentiment: 情感得分 (0-1)
                   - reliability: 可靠性 (可选)
                   - tags: 标签 (可选)
        
        Returns:
            加权情绪分析结果
        """
        if not items:
            return {
                'weighted_score': 0.5,
                'raw_score': 0.5,
                'total_weight': 0,
                'item_count': 0,
                'explanation': '数据不足'
            }
        
        weighted_sum = 0
        weight_sum = 0
        
        # 为每条消息计算权重
        for item in items:
            # 基础情感得分
            sentiment_score = item.get('sentiment', {}).get('score', 0.5)
            created_at = item.get('created_at', '')
            reliability = item.get('reliability', 'unknown')
            tags = item.get('tags', [])
            content = item.get('content', '')
            
            # 时间权重
            time_weight = self.calculate_time_weight(created_at)
            
            # 事件影响力权重
            impact_weight = self.calculate_event_impact_weight(
                content, reliability, tags
            )
            
            # 新鲜度奖励
            freshness_bonus = self.calculate_freshness_bonus(created_at)
            
            # 综合权重 = 时间权重 × 影响力权重 × 新鲜度奖励
            final_weight = time_weight * impact_weight * freshness_bonus
            
            # 加权情感
            weighted_sum += sentiment_score * final_weight
            weight_sum += final_weight
            
            # 保存权重信息用于解释
            item['calculated_weight'] = round(final_weight, 4)
            item['time_weight'] = time_weight
            item['impact_weight'] = impact_weight
            item['freshness_bonus'] = freshness_bonus
        
        # 计算加权平均分
        weighted_score = weighted_sum / weight_sum if weight_sum > 0 else 0.5
        
        # 计算原始平均分 (对比)
        raw_scores = [item.get('sentiment', {}).get('score', 0.5) for item in items]
        raw_score = sum(raw_scores) / len(raw_scores)
        
        # 分析差异
        diff = weighted_score - raw_score
        if diff > 0.05:
            diff_reason = '权重偏向正面消息'
        elif diff < -0.05:
            diff_reason = '权重偏向负面消息'
        else:
            diff_reason = '权重分布相对均衡'
        
        return {
            'weighted_score': round(weighted_score, 3),
            'raw_score': round(raw_score, 3),
            'difference': round(diff, 3),
            'difference_reason': diff_reason,
            'total_weight': round(weight_sum, 3),
            'item_count': len(items),
            'half_life_days': self.half_life_days,
            'explanation': self._generate_explanation(
                weighted_score, raw_score, diff, weight_sum, 
                self.half_life_days, diff_reason
            )
        }
    
    def _generate_explanation(self, weighted: float, raw: float, 
                             diff: float, total_weight: float,
                             half_life: float, diff_reason: str) -> str:
        """生成详细解释"""
        lines = []
        
        lines.append("【时间加权情绪分析】")
        lines.append("")
        lines.append(f"分析方法: 时间衰减 + 事件影响力 + 新鲜度")
        lines.append(f"半衰期设置：{half_life} 天")
        lines.append("")
        lines.append(f"原始情绪得分：{raw:.3f}")
        lines.append(f"加权情绪得分：{weighted:.3f}")
        lines.append(f"差异：{diff:+.3f} ({diff_reason})")
        lines.append("")
        
        if diff > 0.05:
            lines.append("解读:")
            lines.append(f"  加权后得分 {weighted:.3f} > 原始得分 {raw:.3f}")
            lines.append("  说明近期或重大事件偏向正面")
            lines.append("  这个信号比原始平均更有参考价值")
        elif diff < -0.05:
            lines.append("解读:")
            lines.append(f"  加权后得分 {weighted:.3f} < 原始得分 {raw:.3f}")
            lines.append("  说明近期或重大事件偏向负面")
            lines.append("  需要特别关注这些负面信号")
        else:
            lines.append("解读:")
            lines.append("  加权前后差异不大")
            lines.append("  说明情绪分布相对均匀")
        
        return "\n".join(lines)
    
    def analyze_items_with_weights(self, items: List[Dict]) -> str:
        """
        分析并输出详细的权重信息
        
        Args:
            items: 消息列表
        
        Returns:
            格式化的分析文本
        """
        if not items:
            return "数据不足"
        
        result = self.calculate_weighted_sentiment(items)
        
        output = []
        output.append("="*80)
        output.append("时间加权情绪分析详情")
        output.append("="*80)
        output.append("")
        
        # 输出总体结果
        output.append(result['explanation'])
        output.append("")
        
        # 输出每条消息的权重
        output.append("【各消息权重详情】")
        output.append("-"*80)
        
        for i, item in enumerate(items, 1):
            output.append(f"\n{i}. {item.get('content', 'N/A')[:50]}...")
            output.append(f"   原始得分：{item.get('sentiment', {}).get('score', 0):.3f}")
            output.append(f"   时间：{item.get('created_at', 'N/A')[:10]}")
            output.append(f"   时间权重：{item.get('time_weight', 0):.3f}")
            output.append(f"   影响力权重：{item.get('impact_weight', 0):.3f}")
            output.append(f"   新鲜度奖励：{item.get('freshness_bonus', 0):.3f}")
            output.append(f"   最终权重：{item.get('calculated_weight', 0):.3f}")
            
            # 权重来源说明
            factors = []
            if item.get('time_weight', 0) > 0.8:
                factors.append("新消息 ✓")
            elif item.get('time_weight', 0) < 0.3:
                factors.append("旧消息 ⚠️")
            
            if item.get('impact_weight', 0) > 1.3:
                factors.append("重大事件 ✓")
            
            if item.get('freshness_bonus', 0) > 1.1:
                factors.append("24 小时内 ✓")
            
            if factors:
                output.append(f"   特点：{', '.join(factors)}")
        
        output.append("")
        output.append("="*80)
        
        return "\n".join(output)


def demo_time_weighted_analysis():
    """演示时间加权分析"""
    analyzer = TimeWeightedSentiment(half_life_days=7.0)
    
    # 模拟数据
    items = [
        {
            'content': '听说公司最近裁员了',
            'created_at': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
            'sentiment': {'score': 0.234},
            'reliability': 'high',
            'tags': ['财务']
        },
        {
            'content': '供应商说订单减少了',
            'created_at': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S'),
            'sentiment': {'score': 0.312},
            'reliability': 'medium',
            'tags': ['市场']
        },
        {
            'content': '产品大卖 哈哈',
            'created_at': (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S'),
            'sentiment': {'score': 0.856},
            'reliability': 'low',
            'tags': ['产品']
        },
        {
            'content': '公司重大战略转型 AI',
            'created_at': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S'),
            'sentiment': {'score': 0.789},
            'reliability': 'high',
            'tags': ['战略', 'AI']
        },
        {
            'content': '论坛传言有新产品',
            'created_at': (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d %H:%M:%S'),
            'sentiment': {'score': 0.623},
            'reliability': 'low',
            'tags': []
        }
    ]
    
    print("原始数据:")
    print("-"*80)
    for i, item in enumerate(items, 1):
        days = (datetime.now() - datetime.strptime(item['created_at'][:10], '%Y-%m-%d')).days
        print(f"{i}. [{days}天前] {item['content']} - 得分：{item['sentiment']['score']}")
    
    print("\n\n")
    print(analyzer.analyze_items_with_weights(items))
    
    # 对比不同半衰期
    print("\n\n")
    print("【不同半衰期设置对比】")
    print("-"*80)
    
    for half_life in [3, 7, 14, 30]:
        analyzer_test = TimeWeightedSentiment(half_life_days=half_life)
        result = analyzer_test.calculate_weighted_sentiment(items)
        print(f"半衰期 {half_life} 天：加权得分 = {result['weighted_score']:.3f} (原始：{result['raw_score']:.3f}, 差异：{result['difference']:+.3f})")


if __name__ == "__main__":
    demo_time_weighted_analysis()

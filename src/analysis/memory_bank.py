"""
个人观察与记忆库模块

允许用户输入小道消息、个人观察，系统进行分析和记录
支持持续性分析和历史回顾
"""

import json
import os
import sys
from datetime import datetime
from typing import List, Dict

# 添加模块路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.sentiment import analyze_single_sentiment


class MemoryBank:
    """记忆库 - 存储和管理用户的个人观察"""
    
    def __init__(self, symbol: str):
        """
        初始化记忆库
        
        Args:
            symbol: 股票代码
        """
        self.symbol = symbol
        self.memory_file = f"memory_{symbol}.json"
        self.memories = self.load()
    
    def load(self) -> Dict:
        """从文件加载记忆库"""
        if os.path.exists(self.memory_file):
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'symbol': self.symbol,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'observations': [],  # 个人观察
            'rumors': [],  # 小道消息
            'questions': [],  # 疑问
            'decisions': [],  # 决策记录
            'analysis_history': []  # 分析历史
        }
    
    def save(self):
        """保存记忆库到文件"""
        self['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.memories, f, ensure_ascii=False, indent=2)
        print(f"✓ 记忆已保存到：{self.memory_file}")
    
    def add_observation(self, content: str, tags: List[str] = None, 
                       sentiment_analysis: bool = True) -> Dict:
        """
        添加个人观察
        
        Args:
            content: 观察内容
            tags: 标签列表 (如：['产品', '竞争', '管理层'])
            sentiment_analysis: 是否进行情感分析
        
        Returns:
            添加的观察记录
        """
        record = {
            'id': len(self.memories['observations']) + 1,
            'type': 'observation',
            'content': content,
            'tags': tags or [],
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'sentiment': None
        }
        
        # 情感分析
        if sentiment_analysis:
            result = analyze_single_sentiment(content, explain=False)
            record['sentiment'] = {
                'score': result['score'],
                'sentiment': result['sentiment'],
                'sentiment_cn': result['sentiment_cn']
            }
        
        self.memories['observations'].append(record)
        self.save()
        
        print(f"\n✅ 新增观察 #{record['id']}")
        if record['sentiment']:
            emoji = '🟢' if record['sentiment']['sentiment'] == 'positive' else ('🔴' if record['sentiment']['sentiment'] == 'negative' else '⚪')
            print(f"   情感：{emoji} {record['sentiment']['sentiment_cn']} ({record['sentiment']['score']})")
        if tags:
            print(f"   标签：{', '.join(tags)}")
        
        return record
    
    def add_rumor(self, content: str, source: str = '未知', 
                 reliability: str = 'unknown',
                 tags: List[str] = None) -> Dict:
        """
        添加小道消息
        
        Args:
            content: 消息内容
            source: 消息来源 (如：'员工', '供应商', '论坛')
            reliability: 可靠性 ('high', 'medium', 'low', 'unknown')
            tags: 标签列表
        
        Returns:
            添加的消息记录
        """
        # 情感分析
        result = analyze_single_sentiment(content, explain=False)
        
        record = {
            'id': len(self.memories['rumors']) + 1,
            'type': 'rumor',
            'content': content,
            'source': source,
            'reliability': reliability,
            'tags': tags or [],
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'verified': False,
            'sentiment': {
                'score': result['score'],
                'sentiment': result['sentiment'],
                'sentiment_cn': result['sentiment_cn']
            }
        }
        
        self.memories['rumors'].append(record)
        self.save()
        
        print(f"\n✅ 新增小道消息 #{record['id']}")
        print(f"   来源：{source}")
        print(f"   可靠性：{self._reliability_cn(reliability)}")
        emoji = '🟢' if record['sentiment']['sentiment'] == 'positive' else ('🔴' if record['sentiment']['sentiment'] == 'negative' else '⚪')
        print(f"   情感：{emoji} {record['sentiment']['sentiment_cn']} ({record['sentiment']['score']})")
        
        return record
    
    def add_question(self, question: str, answer: str = None, 
                    related_observation_ids: List[int] = None) -> Dict:
        """
        添加疑问
        
        Args:
            question: 问题内容
            answer: 答案 (后续补充)
            related_observation_ids: 相关的观察 ID
        
        Returns:
            添加的疑问记录
        """
        record = {
            'id': len(self.memories['questions']) + 1,
            'type': 'question',
            'question': question,
            'answer': answer,
            'related_observation_ids': related_observation_ids or [],
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'answered': answer is not None
        }
        
        self.memories['questions'].append(record)
        self.save()
        
        print(f"\n❓ 新增疑问 #{record['id']}")
        print(f"   问题：{question}")
        if answer:
            print(f"   答案：{answer}")
        
        return record
    
    def add_decision(self, decision: str, reason: str, 
                    position_change: str = None,
                    related_rumor_ids: List[int] = None) -> Dict:
        """
        添加决策记录
        
        Args:
            decision: 决策内容 (如：'买入', '卖出', '持仓观望')
            reason: 决策理由
            position_change: 仓位变化
            related_rumor_ids: 相关的小道消息 ID
        
        Returns:
            添加的决策记录
        """
        record = {
            'id': len(self.memories['decisions']) + 1,
            'type': 'decision',
            'decision': decision,
            'reason': reason,
            'position_change': position_change,
            'related_rumor_ids': related_rumor_ids or [],
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'outcome': None  # 后续跟踪结果
        }
        
        self.memories['decisions'].append(record)
        self.save()
        
        print(f"\n📝 新增决策 #{record['id']}")
        print(f"   决策：{decision}")
        print(f"   理由：{reason}")
        if position_change:
            print(f"   仓位变化：{position_change}")
        
        return record
    
    def _reliability_cn(self, reliability: str) -> str:
        """可靠性中文翻译"""
        mapping = {
            'high': '高 (可信度高)',
            'medium': '中 (需要验证)',
            'low': '低 (仅供参考)',
            'unknown': '未知'
        }
        return mapping.get(reliability, reliability)
    
    def list_all(self, type_filter: str = None) -> str:
        """
        列出所有记录
        
        Args:
            type_filter: 类型过滤 ('observation', 'rumor', 'question', 'decision')
        
        Returns:
            格式化的列表文本
        """
        output = []
        output.append("="*60)
        output.append(f"记忆库 - {self.symbol}")
        output.append("="*60)
        
        if not type_filter or type_filter == 'observation':
            output.append(f"\n【个人观察】共 {len(self.memories['observations'])} 条")
            for obs in self.memories['observations'][-5:]:  # 最近 5 条
                emoji = '🟢' if obs.get('sentiment', {}).get('sentiment') == 'positive' else ('🔴' if obs.get('sentiment', {}).get('sentiment') == 'negative' else '⚪')
                output.append(f"  #{obs['id']} {emoji} {obs['content'][:50]}... ({obs['created_at'][:10]})")
        
        if not type_filter or type_filter == 'rumor':
            output.append(f"\n【小道消息】共 {len(self.memories['rumors'])} 条")
            for rum in self.memories['rumors'][-5:]:
                emoji = '🟢' if rum.get('sentiment', {}).get('sentiment') == 'positive' else ('🔴' if rum.get('sentiment', {}).get('sentiment') == 'negative' else '⚪')
                output.append(f"  #{rum['id']} {emoji} {rum['content'][:50]}... (来源：{rum['source']})")
        
        if not type_filter or type_filter == 'question':
            output.append(f"\n【疑问】共 {len(self.memories['questions'])} 条")
            for q in self.memories['questions'][-5:]:
                status = '✅' if q['answered'] else '❓'
                output.append(f"  #{q['id']} {status} {q['question'][:50]}...")
        
        if not type_filter or type_filter == 'decision':
            output.append(f"\n【决策记录】共 {len(self.memories['decisions'])} 条")
            for d in self.memories['decisions'][-5:]:
                output.append(f"  #{d['id']} 📝 {d['decision']} - {d['reason'][:30]}...")
        
        return "\n".join(output)
    
    def analyze_trend(self) -> Dict:
        """
        分析情绪趋势
        
        Returns:
            趋势分析结果
        """
        all_items = (
            self.memories['observations'] + 
            self.memories['rumors']
        )
        
        if not all_items:
            return {'trend': 'no_data', 'explanation': '数据不足'}
        
        # 按时间排序
        sorted_items = sorted(all_items, key=lambda x: x['created_at'])
        
        # 分组统计
        recent = sorted_items[-5:] if len(sorted_items) >= 5 else sorted_items
        older = sorted_items[:-5] if len(sorted_items) > 5 else []
        
        # 计算情绪得分
        def avg_score(items):
            if not items:
                return 0.5
            scores = [item.get('sentiment', {}).get('score', 0.5) for item in items if item.get('sentiment')]
            return sum(scores) / len(scores) if scores else 0.5
        
        recent_score = avg_score(recent)
        older_score = avg_score(older)
        
        # 判断趋势
        if recent_score > older_score + 0.1:
            trend = 'improving'
            trend_cn = '向好'
            explanation = f'近期情绪 ({recent_score:.2f}) 明显好于历史 ({older_score:.2f})'
        elif recent_score < older_score - 0.1:
            trend = 'worsening'
            trend_cn = '恶化'
            explanation = f'近期情绪 ({recent_score:.2f}) 明显差于历史 ({older_score:.2f})'
        else:
            trend = 'stable'
            trend_cn = '稳定'
            explanation = f'近期情绪 ({recent_score:.2f}) 与历史 ({older_score:.2f}) 相近'
        
        return {
            'trend': trend,
            'trend_cn': trend_cn,
            'recent_score': round(recent_score, 3),
            'older_score': round(older_score, 3),
            'explanation': explanation
        }
    
    def generate_report(self) -> str:
        """生成完整的记忆库分析报告"""
        report = []
        report.append("="*80)
        report.append(f"个人观察与记忆库分析报告 - {self.symbol}")
        report.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("="*80)
        report.append("")
        
        # 统计信息
        report.append("【统计信息】")
        report.append(f"- 个人观察：{len(self.memories['observations'])} 条")
        report.append(f"- 小道消息：{len(self.memories['rumors'])} 条")
        report.append(f"- 疑问：{len(self.memories['questions'])} 条")
        report.append(f"- 决策记录：{len(self.memories['decisions'])} 条")
        report.append("")
        
        # 情绪趋势
        trend = self.analyze_trend()
        report.append("【情绪趋势分析】")
        report.append(f"- 趋势：{trend['trend_cn']}")
        report.append(f"- 解释：{trend['explanation']}")
        report.append("")
        
        # 最近观察
        if self.memories['observations']:
            report.append("【最近个人观察】")
            for obs in self.memories['observations'][-3:]:
                emoji = '🟢' if obs.get('sentiment', {}).get('sentiment') == 'positive' else ('🔴' if obs.get('sentiment', {}).get('sentiment') == 'negative' else '⚪')
                report.append(f"{emoji} {obs['content']} ({obs['created_at'][:10]})")
            report.append("")
        
        # 小道消息
        if self.memories['rumors']:
            report.append("【小道消息 (按可靠性)】")
            high_rel = [r for r in self.memories['rumors'] if r.get('reliability') == 'high']
            med_rel = [r for r in self.memories['rumors'] if r.get('reliability') == 'medium']
            low_rel = [r for r in self.memories['rumors'] if r.get('reliability') == 'low']
            
            if high_rel:
                report.append("高可靠性:")
                for r in high_rel[-2:]:
                    emoji = '🟢' if r.get('sentiment', {}).get('sentiment') == 'positive' else ('🔴' if r.get('sentiment', {}).get('sentiment') == 'negative' else '⚪')
                    report.append(f"  {emoji} {r['content']} (来源：{r['source']})")
            
            if med_rel:
                report.append("中可靠性:")
                for r in med_rel[-2:]:
                    emoji = '🟢' if r.get('sentiment', {}).get('sentiment') == 'positive' else ('🔴' if r.get('sentiment', {}).get('sentiment') == 'negative' else '⚪')
                    report.append(f"  {emoji} {r['content']} (来源：{r['source']})")
            report.append("")
        
        # 决策记录
        if self.memories['decisions']:
            report.append("【最近决策记录】")
            for d in self.memories['decisions'][-3:]:
                report.append(f"📝 {d['decision']} - {d['reason']}")
            report.append("")
        
        # 综合分析
        report.append("【综合分析建议】")
        report.append("1. 关注情绪趋势变化，特别是连续负面观察")
        report.append("2. 高可靠性小道消息可作为参考，但需要验证")
        report.append("3. 决策记录用于复盘，持续改进投资逻辑")
        report.append("4. 定期回顾疑问，及时补充答案")
        report.append("")
        
        report.append("="*80)
        
        return "\n".join(report)
    
    def __getitem__(self, key):
        return self.memories[key]
    
    def __setitem__(self, key, value):
        self.memories[key] = value


# Interactive CLI
def interactive_memory_cli(symbol: str = "300454"):
    """交互式命令行界面"""
    memory = MemoryBank(symbol)
    
    print("="*60)
    print(f"个人投资记忆库 - {symbol}")
    print("="*60)
    print("Commands:")
    print("  obs <内容> [tags]          - 添加个人观察")
    print("  rumor <内容> [source] [reliability] - 添加小道消息")
    print("  q <问题>                    - 添加疑问")
    print("  dec <决策> <理由>           - 添加决策")
    print("  list [type]                 - 列出记录 (type: obs/rumor/q/dec)")
    print("  report                      - 生成分析报告")
    print("  trend                       - 分析情绪趋势")
    print("  exit                        - 退出")
    print("="*60)
    
    while True:
        try:
            user_input = input("\n> ").strip()
            if not user_input:
                continue
            
            parts = user_input.split(' ', 1)
            cmd = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ''
            
            if cmd in ['exit', 'quit', 'q!']:
                print("再见!")
                break
            
            elif cmd == 'obs':
                content = args
                if not content:
                    print("❌ 请输入观察内容")
                    continue
                # 简单解析 tags
                if '[' in content and ']' in content:
                    start = content.find('[')
                    end = content.find(']')
                    tags_str = content[start+1:end]
                    tags = [t.strip() for t in tags_str.split(',') if t.strip()]
                    content = content[:start].strip()
                else:
                    tags = []
                memory.add_observation(content, tags)
            
            elif cmd == 'rumor':
                # rumor <内容> [来源] [可靠性]
                sub_args = args.split(' ', 2)
                content = sub_args[0]
                source = sub_args[1] if len(sub_args) > 1 else '未知'
                reliability = sub_args[2] if len(sub_args) > 2 else 'unknown'
                if not content:
                    print("❌ 请输入消息内容")
                    continue
                memory.add_rumor(content, source, reliability)
            
            elif cmd == 'q' and len(parts) == 2:
                memory.add_question(args)
            
            elif cmd == 'dec':
                # dec <决策> <理由>
                sub_args = args.split(' ', 1)
                decision = sub_args[0]
                reason = sub_args[1] if len(sub_args) > 1 else ''
                if not decision or not reason:
                    print("❌ 请输入决策和理由")
                    continue
                memory.add_decision(decision, reason)
            
            elif cmd == 'list':
                type_map = {'obs': 'observation', 'rumor': 'rumor', 'q': 'question', 'dec': 'decision'}
                type_filter = type_map.get(args.lower(), None)
                print(memory.list_all(type_filter))
            
            elif cmd == 'report':
                print(memory.generate_report())
            
            elif cmd == 'trend':
                trend = memory.analyze_trend()
                print(f"情绪趋势：{trend['trend_cn']}")
                print(f"解释：{trend['explanation']}")
            
            else:
                print("❌ 未知命令，输入 help 查看帮助")
        
        except KeyboardInterrupt:
            print("\n再见!")
            break
        except Exception as e:
            print(f"❌ 错误：{e}")


if __name__ == "__main__":
    import sys
    symbol = sys.argv[1] if len(sys.argv) > 1 else "300454"
    interactive_memory_cli(symbol)

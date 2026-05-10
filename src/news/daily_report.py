"""
舆情日报生成器

功能:
1. 生成每日舆情摘要 (Markdown 格式)
2. 按信号分类 (买入/卖出/观望)
3. 保存至 output/daily_report/YYYY-MM-DD.md

用法:
    from src.news.daily_report import DailyReportGenerator
    gen = DailyReportGenerator()
    gen.generate(['300454', '600519', '000001'])
"""

import sys
import os
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from news.scanner import SentimentScanner


class DailyReportGenerator:
    """舆情日报生成器"""
    
    def __init__(self, output_dir: str = 'output/daily_reports'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.scanner = SentimentScanner()
        
    def generate(self, symbols: List[str], save: bool = True) -> str:
        """生成日报"""
        # 扫描
        results = self.scanner.scan(symbols)
        
        # 生成 Markdown
        today = datetime.now().strftime('%Y-%m-%d')
        md = self._build_markdown(today, results)
        
        if save:
            path = os.path.join(self.output_dir, f"{today}.md")
            with open(path, 'w', encoding='utf-8') as f:
                f.write(md)
            print(f"\n📄 日报已保存至：{path}")
            
        return md
        
    def _build_markdown(self, date: str, results: List[Dict]) -> str:
        """构建 Markdown 内容"""
        md = f"""# Sentistock 舆情日报

> 日期：{date}  
> 股票数：{len(results)}  
> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 信号汇总

"""
        # 汇总表格
        buy = [r for r in results if r['signal'] == '买入']
        sell = [r for r in results if r['signal'] == '卖出']
        wait = [r for r in results if r['signal'] == '观望']
        
        md += f"| 信号 | 数量 | 占比 |\n"
        md += f"|------|------|------|\n"
        md += f"| 🟢 买入 | {len(buy)} | {len(buy)/len(results)*100:.0f}% |\n"
        md += f"| 🔴 卖出 | {len(sell)} | {len(sell)/len(results)*100:.0f}% |\n"
        md += f"| 🟡 观望 | {len(wait)} | {len(wait)/len(results)*100:.0f}% |\n"
        
        # 买入信号详情
        if buy:
            md += f"\n## 🟢 买入信号 ({len(buy)} 只)\n\n"
            for r in buy:
                md += f"### {r['symbol']}\n"
                md += f"- **情感分数：** {r['avg_score']:.3f}\n"
                md += f"- **新闻数：** {r['news_count']} 条 (正面 {r['pos_count']}, 负面 {r['neg_count']})\n"
                md += f"- **最新新闻：**\n"
                for n in r['news'][:3]:
                    md += f"  - [{n['label']}] {n['title']}\n"
                md += "\n"
                
        # 卖出信号详情
        if sell:
            md += f"\n## 🔴 卖出信号 ({len(sell)} 只)\n\n"
            for r in sell:
                md += f"### {r['symbol']}\n"
                md += f"- **情感分数：** {r['avg_score']:.3f}\n"
                md += f"- **新闻数：** {r['news_count']} 条 (正面 {r['pos_count']}, 负面 {r['neg_count']})\n"
                md += f"- **预警：**\n"
                for a in r.get('alerts', []):
                    md += f"  - {a}\n"
                md += f"- **最新新闻：**\n"
                for n in r['news'][:3]:
                    md += f"  - [{n['label']}] {n['title']}\n"
                md += "\n"
                
        # 观望详情
        if wait:
            md += f"\n## 🟡 观望 ({len(wait)} 只)\n\n"
            for r in wait:
                md += f"### {r['symbol']}\n"
                md += f"- **情感分数：** {r['avg_score']:.3f}\n"
                md += f"- **新闻数：** {r['news_count']} 条\n"
                md += "\n"
                
        # 风险预警
        alerts_total = sum(len(r.get('alerts', [])) for r in results)
        if alerts_total > 0:
            md += f"\n## ⚠️ 风险预警\n\n"
            for r in results:
                if r.get('alerts'):
                    md += f"### {r['symbol']}\n"
                    for a in r['alerts']:
                        md += f"- {a}\n"
                    md += "\n"
                    
        md += f"\n---\n\n*本报告由 Sentistock 自动生成，仅供参考，不构成投资建议。*"
        
        return md


if __name__ == "__main__":
    gen = DailyReportGenerator()
    gen.generate(['300454', '600519', '000001'])

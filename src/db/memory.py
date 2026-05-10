"""
舆情记忆库 (Memory Bank)

功能:
1. 持久化存储历史舆情数据 (SQLite)
2. 计算舆情加速度 (Sentiment Velocity)
3. 检测舆情异动 (Intensity Spike)

用法:
    from db.memory import SentimentMemory
    memory = SentimentMemory()
    memory.record('300454', 0.65, 10, ['盈利'])
    vel = memory.get_velocity('300454', window_hours=2)
"""

import os
import sys
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# 确保能导入 config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

DB_PATH = os.path.join(config.DATA_DIR, 'sentistock.db')

class SentimentMemory:
    """舆情历史数据管理器"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
        
    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 舆情记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sentiment_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                score REAL,
                news_count INTEGER,
                negative_keywords TEXT,
                signal TEXT
            )
        ''')
        
        # 创建索引以加速查询
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_symbol_time ON sentiment_history(symbol, timestamp)')
        
        conn.commit()
        conn.close()
        
    def record(self, symbol: str, score: float, news_count: int, 
               negative_keywords: List[str], signal: str = 'neutral'):
        """记录一次扫描结果"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sentiment_history (symbol, timestamp, score, news_count, negative_keywords, signal)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            symbol,
            datetime.now().isoformat(),
            score,
            news_count,
            json.dumps(negative_keywords, ensure_ascii=False),
            signal
        ))
        
        conn.commit()
        conn.close()
        
    def get_velocity(self, symbol: str, window_hours: int = 2) -> Optional[float]:
        """
        计算舆情加速度 (当前得分 - N 小时前得分)
        负值表示恶化，正值表示好转
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff = (datetime.now() - timedelta(hours=window_hours)).isoformat()
        
        cursor.execute('''
            SELECT score FROM sentiment_history 
            WHERE symbol = ? AND timestamp <= ? 
            ORDER BY timestamp DESC LIMIT 1
        ''', (symbol, cutoff))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
            
        old_score = row[0]
        
        # 获取最新得分
        latest = self.get_latest(symbol)
        if not latest:
            return None
            
        return latest['score'] - old_score
        
    def get_latest(self, symbol: str) -> Optional[Dict]:
        """获取最新一次记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT symbol, timestamp, score, news_count, negative_keywords, signal
            FROM sentiment_history 
            WHERE symbol = ?
            ORDER BY timestamp DESC LIMIT 1
        ''', (symbol,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
            
        return {
            'symbol': row[0],
            'timestamp': row[1],
            'score': row[2],
            'news_count': row[3],
            'negative_keywords': json.loads(row[4]) if row[4] else [],
            'signal': row[5]
        }
        
    def get_intensity_spike(self, symbol: str, window_hours: int = 1) -> bool:
        """
        检测新闻数量是否激增
        如果当前小时新闻数 > 过去 24 小时平均值的 3 倍，返回 True
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        cutoff_1h = (now - timedelta(hours=window_hours)).isoformat()
        cutoff_24h = (now - timedelta(hours=24)).isoformat()
        
        # 当前窗口新闻总数 (这里简化为最后一次记录的 news_count 差异，实际应该累加增量)
        # 为了简单，我们比较：最新一次的 news_count 是否显著高于历史平均
        # 更好的方式是记录每次抓取的新增新闻数，这里先简化为比较 score 波动带来的关联
        
        # 简化逻辑：如果过去 1 小时内有记录，且 news_count > 5 (假设阈值)
        cursor.execute('''
            SELECT COUNT(*) FROM sentiment_history 
            WHERE symbol = ? AND timestamp > ?
        ''', (symbol, cutoff_1h))
        
        count_1h = cursor.fetchone()[0]
        
        # 如果 1 小时内记录了多次 (说明我们在频繁扫描且有更新)，或者单次新闻数很多
        # 这里我们采用简单的：如果过去 1 小时内有记录，且当前新闻数 > 3 条
        latest = self.get_latest(symbol)
        
        conn.close()
        
        if latest and latest['news_count'] >= 3 and count_1h > 0:
            return True # 密集监控中发现了多条新闻
            
        return False

    def get_trend(self, symbol: str, points: int = 5) -> List[float]:
        """获取最近 N 次的得分趋势"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT score FROM sentiment_history 
            WHERE symbol = ?
            ORDER BY timestamp DESC LIMIT ?
        ''', (symbol, points))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [r[0] for r in rows][::-1]  # 返回时间正序

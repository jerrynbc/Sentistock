"""
Sentistock CLI - 统一入口

子命令:
    scan    - 实时舆情扫描
    report  - 生成舆情日报
    backtest - 历史回测 (技术指标模拟)
    score   - 股票评分

用法:
    python src/sentiment_cli.py scan 300454 600519 000001
    python src/sentiment_cli.py report 300454 600519 000001
    python src/sentiment_cli.py backtest 300454 --use-cache
    python src/sentiment_cli.py score 300454 600519 000001
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 默认股票列表
DEFAULT_STOCKS = ['300454', '600519', '000001', '601318', '002594']


def cmd_scan(args):
    """实时舆情扫描"""
    from news.scanner import SentimentScanner
    scanner = SentimentScanner()
    scanner.scan(args.symbols or DEFAULT_STOCKS)


def cmd_report(args):
    """生成舆情日报"""
    from news.daily_report import DailyReportGenerator
    gen = DailyReportGenerator()
    gen.generate(args.symbols or DEFAULT_STOCKS, save=True)


def cmd_backtest(args):
    """历史回测"""
    import subprocess
    cmd = [sys.executable, 'src/analysis/backtest_optimized.py']
    
    if len(args.symbols) == 1:
        cmd.append(args.symbols[0])
        cmd.extend(['--use-cache'])
        if args.real_news:
            cmd.append('--real-news')
    else:
        cmd.append('--multi-test')
        cmd.append('--use-cache')
        
    if args.position_strategy:
        cmd.append('--position-strategy')
        cmd.append(args.position_strategy)
        
    if args.position_pct:
        cmd.append('--position-pct')
        cmd.append(str(args.position_pct))
        
    os.execv(sys.executable, cmd)


def cmd_score(args):
    """股票评分"""
    from analysis.stock_scorer import StockScorer, score_stocks_batch, print_score_summary
    import pandas as pd
    import jqdatasdk as jq
    
    symbols = args.symbols or DEFAULT_STOCKS
    
    # 从缓存加载
    data = {}
    for symbol in symbols:
        cache_path = f"data/cache/{symbol}_2025-01-01_2025-12-31_price.csv"
        if os.path.exists(cache_path):
            df = pd.read_csv(cache_path)
            data[symbol] = df
        else:
            print(f"⚠️ 缓存中无 {symbol} 数据，跳过")
            
    if not data:
        print("❌ 没有可用数据")
        return
        
    scorer = StockScorer()
    results = score_stocks_batch(scorer, data)
    print_score_summary(results)


def cmd_portfolio(args):
    """多股组合回测"""
    from analysis.portfolio_backtest import PortfolioStrategy, prepare_portfolio_data
    from analysis.stock_scorer import StockScorer, score_stocks_batch
    import pandas as pd
    
    symbols = args.stocks or ['300454', '000001']
    
    # 加载缓存数据
    data = {}
    for symbol in symbols:
        cache_path = f"data/cache/{symbol}_2025-01-01_2025-12-31_price.csv"
        if os.path.exists(cache_path):
            data[symbol] = pd.read_csv(cache_path)
        else:
            print(f"⚠️ 缓存中无 {symbol} 数据，跳过")
            
    if not data:
        print("❌ 没有可用数据")
        return
        
    # 准备数据
    prepared_data = {}
    for s, df in data.items():
        prepared_data[s] = prepare_portfolio_data(df, symbol=s, use_real_news=False)
        
    # 计算权重
    weights = {}
    if args.weight == 'equal':
        w = 1.0 / len(prepared_data)
        weights = {s: w for s in prepared_data}
    elif args.weight == 'score':
        scorer = StockScorer()
        scores = score_stocks_batch(scorer, data)
        total = sum(scores[s]['scores']['sentiment_suitability'] for s in prepared_data)
        weights = {s: scores[s]['scores']['sentiment_suitability'] / total for s in prepared_data}
        
    # 运行回测
    strategy = PortfolioStrategy(
        symbols=list(prepared_data.keys()),
        weights=weights,
        initial_capital=args.capital,
        buy_threshold=0.25,
        take_profit_pct=0.20,
        stop_loss_pct=-0.05,
        max_hold_days=20,
    )
    
    results = strategy.run(prepared_data)
    strategy.print_results(results)
    
    # 打印权重分配
    print(f"\n【权重分配】")
    for s, w in weights.items():
        print(f"  {s}: {w*100:.1f}%")


def main():
    parser = argparse.ArgumentParser(
        description='Sentistock - AI 股票分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
子命令:
  scan      实时舆情扫描 (买入/卖出/观望信号)
  report    生成舆情日报 (Markdown)
  backtest  历史回测 (需聚宽账号或缓存)
  score     股票评分 (情绪适用度)
  portfolio 多股组合回测 (等权/评分加权)

示例:
  python src/sentiment_cli.py scan 300454 600519
  python src/sentiment_cli.py report
  python src/sentiment_cli.py backtest 300454
  python src/sentiment_cli.py score 300454 600519 000001
  python src/sentiment_cli.py portfolio --stocks 300454 000001 --weight score
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # scan
    scan_parser = subparsers.add_parser('scan', help='实时舆情扫描')
    scan_parser.add_argument('symbols', nargs='*', help='股票代码')
    scan_parser.set_defaults(func=cmd_scan)
    
    # report
    report_parser = subparsers.add_parser('report', help='生成舆情日报')
    report_parser.add_argument('symbols', nargs='*', help='股票代码')
    report_parser.set_defaults(func=cmd_report)
    
    # backtest
    bt_parser = subparsers.add_parser('backtest', help='历史回测')
    bt_parser.add_argument('symbols', nargs='*', help='股票代码')
    bt_parser.add_argument('--real-news', action='store_true', help='使用真实新闻')
    bt_parser.add_argument('--position-strategy', default='fixed', choices=['fixed', 'kelly'], help='仓位策略')
    bt_parser.add_argument('--position-pct', type=float, default=1.0, help='固定仓位比例')
    bt_parser.set_defaults(func=cmd_backtest)
    
    # score
    score_parser = subparsers.add_parser('score', help='股票评分')
    score_parser.add_argument('symbols', nargs='*', help='股票代码')
    score_parser.set_defaults(func=cmd_score)
    
    # portfolio
    port_parser = subparsers.add_parser('portfolio', help='多股组合回测')
    port_parser.add_argument('--stocks', nargs='*', help='股票代码列表')
    port_parser.add_argument('--weight', default='equal', choices=['equal', 'score'], help='权重方案')
    port_parser.add_argument('--capital', type=float, default=1_000_000, help='初始资金')
    port_parser.set_defaults(func=cmd_portfolio)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
        
    args.func(args)


if __name__ == "__main__":
    main()

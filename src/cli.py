"""
CLI 入口

统一入口，调用 core.py 的功能。
用法:
    python src/cli.py scan 300454 600519
    python src/cli.py report
    python src/cli.py backtest 300454 --advanced
    python src/cli.py portfolio --weight score
    python src/cli.py monitor --symbols 300454
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from core import get_engine


def cmd_scan(args):
    engine = get_engine()
    engine.analyze_sentiment(args.symbols or list(config.DEFAULT_STOCKS.keys())[:5])


def cmd_report(args):
    engine = get_engine()
    engine.generate_report(args.symbols or list(config.DEFAULT_STOCKS.keys())[:5])


def cmd_backtest(args):
    engine = get_engine()
    
    # 登录检查
    if args.user:
        engine.login(args.user, args.password)
    elif not engine.backtester.authenticated:
        # 尝试从环境变量
        engine.login()
        
    symbol = args.symbol
    if not symbol:
        print("❌ 请指定股票代码")
        return
        
    # 确定参数
    params = {}
    if args.optimized:
        params.update(config.OPTIMIZED_PARAMS)
    
    # 获取数据 (如果 backtester 里有缓存)
    # 这里为了简单，直接调用 run_backtest，它会自动去 get_stock_data
    
    res = engine.run_backtest(symbol, use_real_news=args.real_news, use_advanced=args.advanced, **params)
    if res:
        # 打印结果
        if args.advanced:
            from analysis.advanced_strategy import AdvancedTradingStrategy
            AdvancedTradingStrategy().print_results(res)
        else:
            from analysis.backtest_optimized import TradingStrategy
            TradingStrategy().print_results(res)


def cmd_portfolio(args):
    engine = get_engine()
    if args.user:
        engine.login(args.user, args.password)
    elif not engine.backtester.authenticated:
        engine.login()
        
    symbols = args.stocks or ['300454', '000001']
    
    params = {}
    if args.optimized:
        params.update(config.OPTIMIZED_PARAMS)
        
    params['initial_capital'] = args.capital
    
    res = engine.run_portfolio(symbols, weight_type=args.weight, **params)
    
    from analysis.portfolio_backtest import PortfolioStrategy
    PortfolioStrategy(symbols=[], weights={}).print_results(res)


def cmd_monitor(args):
    from core.monitor import MonitorDaemon
    symbols = args.symbols or list(config.DEFAULT_STOCKS.keys())[:3]
    daemon = MonitorDaemon(symbols, interval_minutes=args.interval)
    daemon.run()


def main():
    parser = argparse.ArgumentParser(
        description='Sentistock - AI 股票分析工具',
        epilog="""
示例:
  python src/cli.py scan 300454 600519
  python src/cli.py report
  python src/cli.py backtest 300454 --advanced
  python src/cli.py portfolio --stocks 300454 000001 --weight score --optimized
  python src/cli.py monitor --symbols 300454 600519
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # scan
    scan = subparsers.add_parser('scan', help='舆情扫描')
    scan.add_argument('symbols', nargs='*')
    scan.set_defaults(func=cmd_scan)
    
    # report
    rep = subparsers.add_parser('report', help='舆情日报')
    rep.add_argument('symbols', nargs='*')
    rep.set_defaults(func=cmd_report)
    
    # backtest
    bt = subparsers.add_parser('backtest', help='单股回测')
    bt.add_argument('symbol')
    bt.add_argument('--optimized', action='store_true', help='使用优化参数')
    bt.add_argument('--advanced', action='store_true', help='使用高级策略 (分批止盈)')
    bt.add_argument('--real-news', action='store_true')
    bt.add_argument('--user', help='聚宽账号')
    bt.add_argument('--password', help='聚宽密码')
    bt.set_defaults(func=cmd_backtest)
    
    # portfolio
    port = subparsers.add_parser('portfolio', help='组合回测')
    port.add_argument('--stocks', nargs='*')
    port.add_argument('--weight', default='equal', choices=['equal', 'score'])
    port.add_argument('--optimized', action='store_true')
    port.add_argument('--capital', type=float, default=1_000_000)
    port.add_argument('--user', help='聚宽账号')
    port.add_argument('--password', help='聚宽密码')
    port.set_defaults(func=cmd_portfolio)
    
    # monitor
    mon = subparsers.add_parser('monitor', help='舆情监控守护进程')
    mon.add_argument('--symbols', nargs='*')
    mon.add_argument('--interval', type=int, default=30, help='扫描间隔 (分钟)')
    mon.set_defaults(func=cmd_monitor)
    
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()

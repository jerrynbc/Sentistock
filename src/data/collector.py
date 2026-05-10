"""
股票数据采集模块

提供 A 股历史行情数据获取功能
"""

import pandas as pd
from datetime import datetime, timedelta

# 优先使用 AKShare，如果失败则使用 yfinance
try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False
    print("警告：AKShare 未安装，将使用 yfinance 作为数据源")

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False


def get_stock_history(
    symbol: str,
    start_date: str = None,
    end_date: str = None,
    period: str = "daily",
    use_yfinance: bool = False
) -> pd.DataFrame:
    """
    获取 A 股历史行情数据
    
    Args:
        symbol: 股票代码
            AKShare: "000001" (平安银行)
            yfinance: "000001.SZ" (平安银行)
        start_date: 开始日期，格式 "20230101" 或 "2023-01-01"
        end_date: 结束日期，格式 "20231231" 或 "2023-12-31"
        period: 数据周期，"daily"(日), "weekly"(周), "monthly"(月)
        use_yfinance: 是否强制使用 yfinance
    
    Returns:
        DataFrame 包含以下列：
        - 日期：交易日期
        - 开盘：开盘价
        - 收盘：收盘价
        - 最高：最高价
        - 最低：最低价
        - 成交量：成交股数
        - 成交额：成交金额
    
    Example:
        >>> df = get_stock_history("000001")
        >>> print(df.head())
    """
    if end_date is None:
        end_dt = datetime.now()
        end_date = end_dt.strftime("%Y%m%d")
        end_date_yf = end_dt.strftime("%Y-%m-%d")
    else:
        end_date_yf = end_date[:10] if len(end_date) > 10 else end_date
    
    if start_date is None:
        start_dt = datetime.now() - timedelta(days=365)
        start_date = start_dt.strftime("%Y%m%d")
        start_date_yf = start_dt.strftime("%Y-%m-%d")
    else:
        start_date_yf = start_date[:10] if len(start_date) > 10 else start_date
    
    # 尝试使用 AKShare
    if AKSHARE_AVAILABLE and not use_yfinance:
        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust=""
            )
            print(f"成功获取股票 {symbol} 的数据 (AKShare)，共 {len(df)} 条记录")
            return df
        except Exception as e:
            print(f"AKShare 获取数据失败：{e}")
            if YFINANCE_AVAILABLE:
                print("切换到 yfinance 数据源...")
    
    # 使用 yfinance
    if YFINANCE_AVAILABLE:
        try:
            # A 股代码需要添加后缀
            if symbol.isdigit() and len(symbol) == 6:
                if not symbol.endswith(".SZ") and not symbol.endswith(".SS"):
                    suffix = ".SZ" if symbol.startswith(('0', '3')) else ".SS"
                    yf_symbol = symbol + suffix
                else:
                    yf_symbol = symbol
            else:
                yf_symbol = symbol
            
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(start=start_date_yf, end=end_date_yf)
            
            if df.empty:
                print(f"yfinance 未找到股票 {yf_symbol} 的数据")
                return pd.DataFrame()
            
            # 重命名列以匹配统一格式
            df = df.reset_index()
            df = df.rename(columns={
                'Date': '日期',
                'Open': '开盘',
                'High': '最高',
                'Low': '最低',
                'Close': '收盘',
                'Volume': '成交量'
            })
            df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')
            
            print(f"成功获取股票 {yf_symbol} 的数据 (yfinance)，共 {len(df)} 条记录")
            return df
            
        except Exception as e:
            print(f"yfinance 获取数据失败：{e}")
    
    print("所有数据源均获取失败")
    return pd.DataFrame()


def get_stock_info(symbol: str) -> dict:
    """
    获取股票基本信息
    
    Args:
        symbol: 股票代码
    
    Returns:
        字典包含股票基本信息
    """
    if symbol.isdigit() and len(symbol) == 6:
        if not symbol.endswith(".SZ") and not symbol.endswith(".SS"):
            suffix = ".SZ" if symbol.startswith(('0', '3')) else ".SS"
            symbol = symbol + suffix
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        result = {
            '股票简称': info.get('shortName', ''),
            '行业': info.get('industry', ''),
            '市盈率 (PE)': info.get('trailingPE', ''),
            '市净率 (PB)': info.get('priceToBook', ''),
            '市值': info.get('marketCap', ''),
            '每股收益': info.get('trailingEps', '')
        }
        
        print(f"成功获取股票基本信息")
        return result
        
    except Exception as e:
        print(f"获取基本信息失败：{e}")
        return {}


def get_current_price(symbol: str) -> float:
    """
    获取股票当前价格（实时行情）
    
    Args:
        symbol: 股票代码
    
    Returns:
        当前价格，失败返回 0
    """
    if symbol.isdigit() and len(symbol) == 6:
        suffix = ".SZ" if symbol.startswith(('0', '3')) else ".SS"
        symbol = symbol + suffix
    
    try:
        ticker = yf.Ticker(symbol)
        price = ticker.history(period='1d')['Close'].iloc[-1]
        print(f"股票{symbol} 当前价格：{price}")
        return float(price)
    except Exception as e:
        print(f"获取实时价格失败：{e}")
        return 0.0


if __name__ == "__main__":
    print("=" * 50)
    print("测试数据采集模块")
    print("=" * 50)
    
    symbol = "000001"
    print(f"\n获取股票 {symbol} 的历史数据...\n")
    
    df = get_stock_history(symbol)
    
    if not df.empty:
        print("\n前 5 行数据:")
        print(df.head())
        print("\n数据列:", df.columns.tolist())

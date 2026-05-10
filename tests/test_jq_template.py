#!/usr/bin/env python3
"""
聚宽登录测试脚本
使用前请修改下面的账号密码
"""

import jqdatasdk as jq

# ===== 请修改下面的账号密码 =====
JQ_USERNAME = '你的手机号'   # 替换为你的聚宽手机号
JQ_PASSWORD = '你的密码'     # 替换为你的聚宽密码
# ===============================

print("正在登录聚宽...")
try:
    jq.auth(JQ_USERNAME, JQ_PASSWORD)
    print("✅ 聚宽登录成功！")
    
    # 测试获取股票信息
    print("\n测试获取股票信息...")
    info = jq.get_security_info('300454.XSHE')
    print(f"股票名称：{info.display_name}")
    
    # 测试获取价格
    print("\n测试获取价格数据...")
    price = jq.get_price('300454.XSHE', start_date='2025-12-01', end_date='2025-12-31')
    
    if price is not None and len(price) > 0:
        print(f"✅ 获取到 {len(price)} 条价格数据")
        print(f"12 月收盘价范围：¥{price['close'].min():.2f} - ¥{price['close'].max():.2f}")
        print(f"\n最近 5 天数据:")
        print(price.tail(5)[['open', 'close', 'high', 'low', 'volume']])
    else:
        print("⚠️ 未获取到价格数据")
    
    # 测试查询额度
    print("\n测试查询额度...")
    count = jq.get_query_count()
    print(f"总额度：{count['total']:,}")
    print(f"剩余：{count['spare']:,}")
    
    print("\n✅ 聚宽 SDK 测试完成！")
    
except Exception as e:
    print(f"❌ 测试失败：{e}")
    print("\n请检查:")
    print("1. 账号密码是否正确")
    print("2. 是否已注册聚宽账号 (https://www.joinquant.com/)")
    print("3. 网络连接是否正常")

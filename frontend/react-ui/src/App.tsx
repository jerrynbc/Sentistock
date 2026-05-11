import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// 模拟数据
const mockStockData = [
  { date: '2025-01', value: 100 },
  { date: '2025-02', value: 120 },
  { date: '2025-03', value: 90 },
  { date: '2025-04', value: 140 },
  { date: '2025-05', value: 160 },
];

const mockBacktestResults = [
  { symbol: '300454', return: '7860.60%', winRate: '53.3%' },
  { symbol: '688561', return: '3655.84%', winRate: '60.0%' },
  { symbol: '002371', return: '6087.82%', winRate: '55.0%' },
];

function App() {
  const [selectedStocks, setSelectedStocks] = useState<string[]>(['300454']);
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900">Sentistock AI股票分析系统</h1>
          <p className="mt-2 text-gray-600">基于多模型集成的智能股票筛选与交易策略</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
        {/* Stock Selection */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">股票选择</h2>
          <div className="flex flex-wrap gap-2">
            {['300454', '688561', '002371', '600011', '002230'].map((symbol) => (
              <button
                key={symbol}
                onClick={() => setSelectedStocks([symbol])}
                className={`px-4 py-2 rounded-full text-sm font-medium ${
                  selectedStocks.includes(symbol)
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {symbol}
              </button>
            ))}
          </div>
        </div>

        {/* Dashboard Tabs */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Stock Scoring */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">股票价值评分</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">综合评分</span>
                <span className="font-semibold text-green-600">82.2</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">波动性</span>
                <span className="font-semibold">85/100</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">趋势强度</span>
                <span className="font-semibold">78/100</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">建议</span>
                <span className="font-semibold text-green-600">高价值</span>
              </div>
            </div>
          </div>

          {/* Backtest Results */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">回测分析结果</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">累计收益</span>
                <span className="font-semibold text-green-600">7860.60%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">胜率</span>
                <span className="font-semibold">53.3%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">最大回撤</span>
                <span className="font-semibold text-red-600">-7.80%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">交易次数</span>
                <span className="font-semibold">15</span>
              </div>
            </div>
          </div>

          {/* Real-time Monitoring */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">实时舆情监控</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">当前舆情分数</span>
                <span className="font-semibold">0.78</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">2小时加速度</span>
                <span className="font-semibold text-yellow-600">-0.12</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">持仓状态</span>
                <span className="font-semibold text-green-600">持有</span>
              </div>
            </div>
          </div>
        </div>

        {/* Chart Section */}
        <div className="bg-white shadow rounded-lg p-6 mt-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">策略收益对比</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={mockStockData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="value" stroke="#3b82f6" activeDot={{ r: 8 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Multi-stock Results */}
        <div className="bg-white shadow rounded-lg p-6 mt-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">多股票回测结果</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">股票代码</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">累计收益</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">胜率</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {mockBacktestResults.map((stock) => (
                  <tr key={stock.symbol}>
                    <td className="px-6 py-4 whitespace-nowrap">{stock.symbol}</td>
                    <td className="px-6 py-4 whitespace-nowrap font-semibold text-green-600">{stock.return}</td>
                    <td className="px-6 py-4 whitespace-nowrap">{stock.winRate}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-8">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <p className="text-center text-gray-500 text-sm">
            Sentistock v1.0 - AI驱动的股票分析系统 | 数据更新: 2025-12-31
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
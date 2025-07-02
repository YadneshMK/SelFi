'use client';

import { useEffect, useState, useMemo, useCallback } from 'react';
import Layout from '@/components/Layout';
import api from '@/lib/api';
import { NetworkError } from '@/lib/network-monitor';
import { InfoTooltip } from '@/components/InfoTooltip';
import { debugAuth } from '@/lib/debug-auth';
import { TrendingUp, TrendingDown, IndianRupee, PieChart, BarChart3, RefreshCw, WifiOff, AlertCircle } from 'lucide-react';
import { PieChart as ReChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend, Sector } from 'recharts';

interface PortfolioSummary {
  total_value: number;
  total_investment: number;
  total_pnl: number;
  total_pnl_percentage: number;
  holdings_count: number;
  asset_allocation: Record<string, number>;
  platform_allocation: Record<string, number>;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

// Custom active shape for pie chart hover effect
const renderActiveShape = (props: any) => {
  const { cx, cy, innerRadius, outerRadius, startAngle, endAngle, fill } = props;
  
  return (
    <g>
      <Sector
        cx={cx}
        cy={cy}
        innerRadius={innerRadius}
        outerRadius={outerRadius + 6}
        startAngle={startAngle}
        endAngle={endAngle}
        fill={fill}
      />
    </g>
  );
};

const renderCustomLegend = (props: any) => {
  const { payload } = props;
  
  return (
    <div className="flex flex-wrap justify-center gap-x-4 gap-y-2 mt-4">
      {payload.map((entry: any, index: number) => (
        <div key={`item-${index}`} className="flex items-center">
          <span 
            className="inline-block w-3 h-3 rounded-full mr-1"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-xs text-gray-600">
            {entry.value}: {entry.payload.value}%
          </span>
        </div>
      ))}
    </div>
  );
};

export default function DashboardPage() {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<'network' | 'api' | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeAssetIndex, setActiveAssetIndex] = useState<number>(-1);
  const [activePlatformIndex, setActivePlatformIndex] = useState<number>(-1);

  // Define all useCallback hooks before any conditional returns
  const formatCurrency = useCallback((value: number, decimals: number = 0) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(value);
  }, []);

  const formatPercentage = useCallback((value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  }, []);

  const formatAssetType = useCallback((type: string) => {
    const formatted = {
      'stock': 'Stocks',
      'etf': 'ETFs',
      'mutual_fund': 'Mutual Funds',
      'sgb': 'Sovereign Gold Bonds',
      'reit': 'REITs'
    };
    return formatted[type.toLowerCase()] || type.replace('_', ' ').toUpperCase();
  }, []);

  const formatPlatformName = useCallback((platform: string) => {
    const formatted = {
      'zerodha': 'Zerodha',
      'groww': 'Groww',
      'upstox': 'Upstox',
      'paytm_money': 'Paytm Money',
      'coin': 'Coin'
    };
    return formatted[platform.toLowerCase()] || platform;
  }, []);

  // Define useMemo hooks before conditional returns
  const assetData = useMemo(() => {
    if (!summary) return [];
    return Object.entries(summary.asset_allocation).map(([name, value]) => ({
      name: formatAssetType(name),
      value: parseFloat(value.toFixed(2))
    }));
  }, [summary, formatAssetType]);

  const platformData = useMemo(() => {
    if (!summary) return [];
    return Object.entries(summary.platform_allocation).map(([name, value]) => ({
      name: formatPlatformName(name),
      value: parseFloat(value.toFixed(2))
    }));
  }, [summary, formatPlatformName]);

  useEffect(() => {
    // Debug auth on mount
    debugAuth();
    fetchSummary();
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;
    
    // Auto-refresh every 30 seconds when tab is visible
    const interval = setInterval(() => {
      if (!document.hidden) {
        fetchSummary();
      }
    }, 30000);
    
    return () => clearInterval(interval);
  }, [autoRefresh]);

  const fetchSummary = async () => {
    try {
      setError(null);
      setErrorType(null);
      setRefreshing(true);
      console.log('Fetching dashboard summary...');
      const response = await api.get('/portfolios/summary');
      console.log('Dashboard summary response:', response.data);
      setSummary(response.data);
      setLastUpdated(new Date());
    } catch (error: any) {
      console.error('Failed to fetch summary:', error);
      if (error instanceof NetworkError) {
        setErrorType('network');
        setError(error.message);
      } else if (error.response?.status === 401) {
        setErrorType('api');
        setError('Session expired. Please login again.');
        // Don't redirect here, let the interceptor handle it
      } else {
        setErrorType('api');
        setError(error.response?.data?.detail || 'Failed to load dashboard data. Please try again.');
      }
      setSummary(null); // Clear summary on error
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="min-h-[400px] flex items-center justify-center">
          <div className="text-center max-w-md">
            <div className={`mx-auto flex items-center justify-center h-12 w-12 rounded-full ${
              errorType === 'network' ? 'bg-yellow-100' : 'bg-red-100'
            }`}>
              {errorType === 'network' ? (
                <WifiOff className="h-6 w-6 text-yellow-600" />
              ) : (
                <AlertCircle className="h-6 w-6 text-red-600" />
              )}
            </div>
            <h3 className="mt-2 text-lg font-medium text-gray-900">
              {errorType === 'network' ? 'Connection Problem' : 'Error Loading Dashboard'}
            </h3>
            <p className="mt-1 text-sm text-gray-500">{error}</p>
            {errorType === 'network' && (
              <p className="mt-2 text-xs text-gray-400">
                Check your internet connection and try again
              </p>
            )}
            <div className="mt-6 space-x-3">
              <button
                onClick={() => {
                  setError(null);
                  setErrorType(null);
                  setLoading(true);
                  fetchSummary();
                }}
                disabled={refreshing}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
              >
                <RefreshCw className={`mr-2 h-5 w-5 ${refreshing ? 'animate-spin' : ''}`} />
                Try Again
              </button>
              {errorType === 'api' && (
                <button
                  onClick={() => window.location.reload()}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Reload Page
                </button>
              )}
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6 overflow-x-hidden">
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center space-y-4 sm:space-y-0">
          <h1 className="text-2xl font-semibold text-gray-900">Portfolio Dashboard</h1>
          <div className="flex flex-col sm:flex-row sm:items-center space-y-2 sm:space-y-0 sm:space-x-4">
            {lastUpdated && (
              <span className="text-sm text-gray-500 whitespace-nowrap">
                Last updated: {lastUpdated.toLocaleTimeString('en-US', { hour12: false })}
              </span>
            )}
            <div className="flex items-center space-x-2">
              <label className="flex items-center text-sm text-gray-600">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="mr-2 h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  aria-label="Toggle auto-refresh"
                />
                Auto-refresh
              </label>
              <button
                onClick={() => fetchSummary()}
                disabled={refreshing}
                className="inline-flex items-center px-3 py-1.5 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label="Refresh data"
              >
                <RefreshCw className={`h-5 w-5 mr-1 ${refreshing ? 'animate-spin' : ''}`} />
                <span className="hidden sm:inline">{refreshing ? 'Refreshing...' : 'Refresh'}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 md:grid-cols-2 lg:grid-cols-4">
          <div className="bg-white shadow rounded-lg relative">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <IndianRupee className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 min-w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 flex items-center">
                      Total Value
                      <InfoTooltip text="The current market value of all your holdings across all platforms" />
                    </dt>
                    <dd className="text-lg font-semibold text-gray-900">
                      {summary?.total_value === 0 ? (
                        <span className="text-gray-400">No investments yet</span>
                      ) : (
                        formatCurrency(summary?.total_value || 0)
                      )}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white shadow rounded-lg relative">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <BarChart3 className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 min-w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 flex items-center">
                      Total Investment
                      <InfoTooltip text="The total amount you've invested to purchase all your holdings" />
                    </dt>
                    <dd className="text-lg font-semibold text-gray-900">
                      {formatCurrency(summary?.total_investment || 0)}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white shadow rounded-lg relative">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  {(summary?.total_pnl || 0) >= 0 ? (
                    <TrendingUp className="h-6 w-6 text-green-500" />
                  ) : (
                    <TrendingDown className="h-6 w-6 text-red-500" />
                  )}
                </div>
                <div className="ml-5 min-w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 flex items-center">
                      Total P&L
                      <InfoTooltip text="Profit & Loss: The difference between current value and total investment" />
                    </dt>
                    <dd className={`text-lg font-semibold ${
                      summary?.total_investment === 0 ? 'text-gray-400' :
                      (summary?.total_pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {summary?.total_investment === 0 ? (
                        <span>No P&L data</span>
                      ) : (
                        <>
                          {formatCurrency(summary?.total_pnl || 0)}
                          <span className="text-sm ml-2">
                            ({formatPercentage(summary?.total_pnl_percentage || 0)})
                          </span>
                        </>
                      )}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white shadow rounded-lg relative">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <PieChart className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 min-w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 flex items-center">
                      Holdings
                      <InfoTooltip text="The total number of unique securities you own across all platforms" />
                    </dt>
                    <dd className="text-lg font-semibold text-gray-900">
                      {summary?.holdings_count || 0}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-2 overflow-hidden">
          {/* Asset Allocation */}
          <div className="bg-white shadow rounded-lg p-6 overflow-hidden">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Asset Allocation</h2>
            {assetData.length > 0 ? (
              <ResponsiveContainer width="100%" aspect={1.5}>
                <ReChart role="img" aria-label="Asset allocation pie chart" style={{ outline: 'none' }}>
                  <Pie
                    data={assetData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius="70%"
                    fill="#8884d8"
                    dataKey="value"
                    isAnimationActive={false}
                    activeIndex={-1}
                    activeShape={undefined}
                  >
                    {assetData.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={COLORS[index % COLORS.length]}
                        stroke="none"
                      />
                    ))}
                  </Pie>
                  <Legend 
                    content={renderCustomLegend}
                  />
                </ReChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center text-gray-500 py-12">
                No holdings data available
              </div>
            )}
          </div>

          {/* Platform Allocation */}
          <div className="bg-white shadow rounded-lg p-6 overflow-hidden">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Platform Allocation</h2>
            {platformData.length > 0 ? (
              <ResponsiveContainer width="100%" aspect={1.5}>
                <ReChart role="img" aria-label="Platform allocation pie chart" style={{ outline: 'none' }}>
                  <Pie
                    data={platformData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius="70%"
                    fill="#8884d8"
                    dataKey="value"
                    isAnimationActive={false}
                    activeIndex={-1}
                    activeShape={undefined}
                  >
                    {platformData.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={COLORS[index % COLORS.length]}
                        stroke="none"
                      />
                    ))}
                  </Pie>
                  <Legend 
                    content={renderCustomLegend}
                  />
                </ReChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center text-gray-500 py-12">
                No platform data available
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        {(!summary || summary.holdings_count === 0) && (
          <div className={`${summary?.total_investment > 0 ? 'bg-yellow-50 border-yellow-400' : 'bg-blue-50 border-blue-400'} border-l-4 p-4 rounded-lg`}>
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className={`h-5 w-5 ${summary?.total_investment > 0 ? 'text-yellow-400' : 'text-blue-400'}`} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className={`text-sm font-medium ${summary?.total_investment > 0 ? 'text-yellow-800' : 'text-blue-800'}`}>
                  {summary?.total_investment > 0 ? 'No Active Holdings Found' : 'Welcome to Finance Tracker!'}
                </h3>
                <div className={`mt-2 text-sm ${summary?.total_investment > 0 ? 'text-yellow-700' : 'text-blue-700'}`}>
                  {summary?.total_investment > 0 ? (
                    <>
                      <p>It looks like you had investments before but currently have no active holdings.</p>
                      <p className="mt-2">You can upload new portfolio data to track your investments.</p>
                    </>
                  ) : (
                    <>
                      <p>Start by uploading your portfolio data from Zerodha Console, Groww, or other platforms.</p>
                      <p className="mt-2">You can upload:</p>
                      <ul className="list-disc list-inside mt-1 ml-2">
                        <li>Holdings CSV from your broker</li>
                        <li>Transaction history</li>
                        <li>Excel files with portfolio data</li>
                      </ul>
                    </>
                  )}
                  <a href="/dashboard/upload" className={`inline-flex items-center px-4 py-2 mt-4 border border-transparent text-sm font-medium rounded-md shadow-sm text-white ${
                    summary?.total_investment > 0 ? 'bg-indigo-600 hover:bg-indigo-700 focus:ring-indigo-500' : 'bg-indigo-600 hover:bg-indigo-700 focus:ring-indigo-500'
                  } focus:outline-none focus:ring-2 focus:ring-offset-2`}>
                    {summary?.total_investment > 0 ? 'Upload New Portfolio →' : 'Upload Your First Portfolio →'}
                  </a>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
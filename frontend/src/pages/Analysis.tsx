/**
 * Analysis Page for OSINT Platform
 * Displays data analysis results and AI-powered insights
 */

import React, { useState } from 'react';
import { useQuery } from 'react-query';
import {
  ChartBarIcon,
  CpuChipIcon,
  PlayIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { api } from '../services/api';
import { PieChart, Pie, Cell, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const Analysis: React.FC = () => {
  const [selectedTimeframe, setSelectedTimeframe] = useState('7d');
  
  // Fetch sentiment analysis data
  const { data: sentimentData, isLoading: sentimentLoading } = useQuery(
    'sentimentAnalysis',
    api.analysis.getSentimentAnalysis
  );

  // Sample data for charts
  const sentimentBreakdown = [
    { name: 'Positive', value: 65, color: '#10b981' },
    { name: 'Neutral', value: 25, color: '#6b7280' },
    { name: 'Negative', value: 10, color: '#ef4444' },
  ];

  const trendData = [
    { date: '2024-01-01', mentions: 120, sentiment: 0.7 },
    { date: '2024-01-02', mentions: 135, sentiment: 0.65 },
    { date: '2024-01-03', mentions: 98, sentiment: 0.72 },
    { date: '2024-01-04', mentions: 156, sentiment: 0.68 },
    { date: '2024-01-05', mentions: 189, sentiment: 0.75 },
    { date: '2024-01-06', mentions: 167, sentiment: 0.71 },
    { date: '2024-01-07', mentions: 201, sentiment: 0.78 },
  ];

  const topKeywords = [
    { keyword: 'innovation', count: 45, sentiment: 0.8 },
    { keyword: 'market', count: 38, sentiment: 0.6 },
    { keyword: 'competitor', count: 32, sentiment: -0.2 },
    { keyword: 'product', count: 29, sentiment: 0.7 },
    { keyword: 'technology', count: 26, sentiment: 0.9 },
  ];

  const handleTriggerAnalysis = async () => {
    try {
      await api.analysis.triggerAnalysis();
      // Refresh data after triggering analysis
    } catch (error) {
      console.error('Failed to trigger analysis:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analysis</h1>
          <p className="mt-2 text-gray-600">
            AI-powered insights from your OSINT data collection.
          </p>
        </div>
        <div className="flex space-x-4">
          <select
            value={selectedTimeframe}
            onChange={(e) => setSelectedTimeframe(e.target.value)}
            className="input-field w-auto"
          >
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
          </select>
          <button
            onClick={handleTriggerAnalysis}
            className="btn-primary flex items-center"
          >
            <PlayIcon className="h-5 w-5 mr-2" />
            Run Analysis
          </button>
        </div>
      </div>

      {/* Analysis Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ChartBarIcon className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Overall Sentiment</p>
              <p className="text-2xl font-bold text-gray-900">
                {sentimentLoading ? '...' : (sentimentData?.sentiment_score * 100).toFixed(1)}%
              </p>
              <p className="text-sm text-green-600">Positive trend</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CpuChipIcon className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Analysis Confidence</p>
              <p className="text-2xl font-bold text-gray-900">
                {sentimentLoading ? '...' : (sentimentData?.confidence * 100).toFixed(1)}%
              </p>
              <p className="text-sm text-blue-600">High confidence</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ArrowPathIcon className="h-8 w-8 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Last Updated</p>
              <p className="text-lg font-semibold text-gray-900">2 hours ago</p>
              <p className="text-sm text-gray-500">
                {sentimentLoading ? '...' : new Date(sentimentData?.analysis_date).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sentiment Breakdown */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">Sentiment Breakdown</h3>
            <p className="text-sm text-gray-600">Distribution of sentiment across all data points</p>
          </div>
          <div className="h-80 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={sentimentBreakdown}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={120}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}%`}
                >
                  {sentimentBreakdown.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Trend Analysis */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">Mention & Sentiment Trends</h3>
            <p className="text-sm text-gray-600">Volume and sentiment over time</p>
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Area
                  yAxisId="left"
                  type="monotone"
                  dataKey="mentions"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.3}
                  name="Mentions"
                />
                <Area
                  yAxisId="right"
                  type="monotone"
                  dataKey="sentiment"
                  stroke="#10b981"
                  fill="#10b981"
                  fillOpacity={0.3}
                  name="Sentiment Score"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Top Keywords */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-gray-900">Top Keywords</h3>
          <p className="text-sm text-gray-600">Most mentioned keywords and their sentiment</p>
        </div>
        <div className="overflow-hidden">
          <table className="table">
            <thead>
              <tr>
                <th>Keyword</th>
                <th>Mentions</th>
                <th>Sentiment</th>
                <th>Trend</th>
              </tr>
            </thead>
            <tbody>
              {topKeywords.map((keyword, index) => (
                <tr key={index}>
                  <td className="font-medium">{keyword.keyword}</td>
                  <td>{keyword.count}</td>
                  <td>
                    <span className={`badge ${
                      keyword.sentiment > 0.5 ? 'success' :
                      keyword.sentiment > 0 ? 'warning' : 'error'
                    }`}>
                      {keyword.sentiment > 0.5 ? 'Positive' :
                       keyword.sentiment > 0 ? 'Neutral' : 'Negative'}
                    </span>
                  </td>
                  <td>
                    <div className="flex items-center">
                      <div className="w-16 h-8 bg-gray-100 rounded">
                        {/* Mini trend chart placeholder */}
                        <div className="w-full h-full bg-gradient-to-r from-blue-500 to-green-500 rounded opacity-30"></div>
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* AI Insights */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-gray-900">AI Insights</h3>
          <p className="text-sm text-gray-600">Automated insights from your data</p>
        </div>
        <div className="space-y-4">
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h4 className="font-medium text-blue-900 mb-2">📈 Positive Trend Detected</h4>
            <p className="text-blue-800 text-sm">
              Sentiment has increased by 15% over the past week, with particularly strong positive 
              mentions around 'innovation' and 'technology' keywords.
            </p>
          </div>
          
          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <h4 className="font-medium text-yellow-900 mb-2">⚠️ Competitor Activity</h4>
            <p className="text-yellow-800 text-sm">
              Increased mentions of competitor brands detected. Consider monitoring for 
              potential market shifts or competitive responses.
            </p>
          </div>
          
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <h4 className="font-medium text-green-900 mb-2">✅ Strong Market Perception</h4>
            <p className="text-green-800 text-sm">
              Your brand maintains strong positive sentiment (78%) with consistently 
              high engagement rates across all monitored channels.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analysis;

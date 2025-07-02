/**
 * Dashboard Page for OSINT Platform
 * Main overview page with metrics, charts, and recent activity
 */

import React from 'react';
import { useQuery } from 'react-query';
import {
  ChartBarIcon,
  DocumentTextIcon,
  BellIcon,
  ServerIcon,
  TrendingUpIcon,
  TrendingDownIcon,
} from '@heroicons/react/24/outline';
import { api } from '../services/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

const Dashboard: React.FC = () => {
  // Fetch dashboard data
  const { data: metrics, isLoading: metricsLoading } = useQuery(
    'dashboardMetrics',
    api.dashboard.getMetrics,
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  const { data: activityData, isLoading: activityLoading } = useQuery(
    'recentActivity',
    api.dashboard.getRecentActivity,
    {
      refetchInterval: 60000, // Refresh every minute
    }
  );

  // Sample data for charts
  const sentimentData = [
    { date: '2024-01-01', positive: 65, negative: 25, neutral: 10 },
    { date: '2024-01-02', positive: 70, negative: 20, neutral: 10 },
    { date: '2024-01-03', positive: 68, negative: 22, neutral: 10 },
    { date: '2024-01-04', positive: 72, negative: 18, neutral: 10 },
    { date: '2024-01-05', positive: 75, negative: 15, neutral: 10 },
    { date: '2024-01-06', positive: 73, negative: 17, neutral: 10 },
    { date: '2024-01-07', positive: 78, negative: 12, neutral: 10 },
  ];

  const dataVolumeData = [
    { date: '2024-01-01', volume: 1250 },
    { date: '2024-01-02', volume: 1180 },
    { date: '2024-01-03', volume: 1420 },
    { date: '2024-01-04', volume: 1350 },
    { date: '2024-01-05', volume: 1680 },
    { date: '2024-01-06', volume: 1520 },
    { date: '2024-01-07', volume: 1750 },
  ];

  if (metricsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Welcome back! Here's what's happening with your OSINT operations.
        </p>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="metric-card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ServerIcon className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Data Sources</p>
              <p className="metric-value">{metrics?.total_sources || 0}</p>
              <p className="metric-change positive flex items-center">
                <TrendingUpIcon className="h-4 w-4 mr-1" />
                +2 this week
              </p>
            </div>
          </div>
        </div>

        <div className="metric-card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <BellIcon className="h-8 w-8 text-yellow-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Active Alerts</p>
              <p className="metric-value">{metrics?.active_alerts || 0}</p>
              <p className="metric-change negative flex items-center">
                <TrendingDownIcon className="h-4 w-4 mr-1" />
                -1 from yesterday
              </p>
            </div>
          </div>
        </div>

        <div className="metric-card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ChartBarIcon className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Analyses</p>
              <p className="metric-value">{metrics?.recent_analyses || 0}</p>
              <p className="metric-change positive flex items-center">
                <TrendingUpIcon className="h-4 w-4 mr-1" />
                +5 today
              </p>
            </div>
          </div>
        </div>

        <div className="metric-card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <DocumentTextIcon className="h-8 w-8 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Data Points</p>
              <p className="metric-value">
                {metrics?.data_points_collected?.toLocaleString() || 0}
              </p>
              <p className="metric-change positive flex items-center">
                <TrendingUpIcon className="h-4 w-4 mr-1" />
                +247 today
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sentiment Trend Chart */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">Sentiment Trends</h3>
            <p className="text-sm text-gray-600">7-day sentiment analysis overview</p>
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={sentimentData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="positive"
                  stroke="#10b981"
                  strokeWidth={2}
                  name="Positive"
                />
                <Line
                  type="monotone"
                  dataKey="negative"
                  stroke="#ef4444"
                  strokeWidth={2}
                  name="Negative"
                />
                <Line
                  type="monotone"
                  dataKey="neutral"
                  stroke="#6b7280"
                  strokeWidth={2}
                  name="Neutral"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Data Volume Chart */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">Data Collection Volume</h3>
            <p className="text-sm text-gray-600">Daily data points collected</p>
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dataVolumeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="volume" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-gray-900">Recent Activity</h3>
          <p className="text-sm text-gray-600">Latest platform activities and updates</p>
        </div>
        
        {activityLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <div className="space-y-4">
            {activityData?.activities?.map((activity, index) => (
              <div key={index} className="flex items-start space-x-3 p-4 bg-gray-50 rounded-lg">
                <div className="flex-shrink-0">
                  <div className="w-2 h-2 bg-blue-600 rounded-full mt-2"></div>
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">
                    {activity.description}
                  </p>
                  <p className="text-xs text-gray-500">
                    {new Date(activity.timestamp).toLocaleString()}
                  </p>
                </div>
                <div className="flex-shrink-0">
                  <span className={`badge ${
                    activity.type === 'data_collection' ? 'info' :
                    activity.type === 'analysis' ? 'success' :
                    activity.type === 'alert' ? 'warning' : 'info'
                  }`}>
                    {activity.type.replace('_', ' ')}
                  </span>
                </div>
              </div>
            )) || (
              <p className="text-gray-500 text-center py-8">
                No recent activity to display
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;

/**
 * Reports Page for OSINT Platform
 * Manages report generation and viewing
 */

import React, { useState } from 'react';
import { useQuery } from 'react-query';
import {
  DocumentTextIcon,
  PlusIcon,
  ArrowDownTrayIcon,
  EyeIcon,
  CalendarIcon,
} from '@heroicons/react/24/outline';
import { api } from '../services/api';

const Reports: React.FC = () => {
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  
  // Fetch reports
  const { data: reportsData, isLoading } = useQuery(
    'reports',
    api.reports.list
  );

  const reports = reportsData?.reports || [];

  const handleGenerateReport = async () => {
    try {
      await api.reports.generate();
      setShowGenerateModal(false);
      // Refresh reports list
    } catch (error) {
      console.error('Failed to generate report:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Reports</h1>
          <p className="mt-2 text-gray-600">
            Generate and manage comprehensive OSINT analysis reports.
          </p>
        </div>
        <button
          onClick={() => setShowGenerateModal(true)}
          className="btn-primary flex items-center"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          Generate Report
        </button>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">{reports.length}</p>
            <p className="text-sm text-gray-600">Total Reports</p>
          </div>
        </div>
        <div className="card">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">3</p>
            <p className="text-sm text-gray-600">This Month</p>
          </div>
        </div>
        <div className="card">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">1.2GB</p>
            <p className="text-sm text-gray-600">Total Size</p>
          </div>
        </div>
        <div className="card">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">98%</p>
            <p className="text-sm text-gray-600">Success Rate</p>
          </div>
        </div>
      </div>

      {/* Reports List */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-gray-900">Recent Reports</h3>
          <p className="text-sm text-gray-600">View and download your generated reports</p>
        </div>
        
        {reports.length > 0 ? (
          <div className="overflow-hidden">
            <table className="table">
              <thead>
                <tr>
                  <th>Report</th>
                  <th>Type</th>
                  <th>Created</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {reports.map((report) => (
                  <tr key={report.id}>
                    <td>
                      <div className="flex items-center">
                        <DocumentTextIcon className="h-5 w-5 text-gray-400 mr-3" />
                        <div>
                          <p className="font-medium text-gray-900">{report.title}</p>
                          <p className="text-sm text-gray-500">ID: {report.id}</p>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className="badge info capitalize">{report.type}</span>
                    </td>
                    <td>{new Date(report.created_at).toLocaleDateString()}</td>
                    <td>
                      <span className={`badge ${
                        report.status === 'completed' ? 'success' :
                        report.status === 'processing' ? 'warning' :
                        report.status === 'failed' ? 'error' : 'info'
                      }`}>
                        {report.status}
                      </span>
                    </td>
                    <td>
                      <div className="flex space-x-2">
                        <button className="p-1 text-gray-400 hover:text-blue-600">
                          <EyeIcon className="h-5 w-5" />
                        </button>
                        <button className="p-1 text-gray-400 hover:text-green-600">
                          <ArrowDownTrayIcon className="h-5 w-5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12">
            <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No reports</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by generating your first report.
            </p>
            <div className="mt-6">
              <button
                onClick={() => setShowGenerateModal(true)}
                className="btn-primary"
              >
                <PlusIcon className="h-5 w-5 mr-2" />
                Generate Report
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Generate Report Modal */}
      {showGenerateModal && (
        <div className="modal-overlay" onClick={() => setShowGenerateModal(false)}>
          <div className="modal-content max-w-lg" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Generate New Report
            </h3>
            
            <form className="space-y-4">
              <div>
                <label className="label">Report Type</label>
                <select className="input-field">
                  <option value="competitive">Competitive Analysis</option>
                  <option value="sentiment">Sentiment Analysis</option>
                  <option value="comprehensive">Comprehensive Overview</option>
                  <option value="custom">Custom Report</option>
                </select>
              </div>
              
              <div>
                <label className="label">Time Period</label>
                <select className="input-field">
                  <option value="7d">Last 7 days</option>
                  <option value="30d">Last 30 days</option>
                  <option value="90d">Last 90 days</option>
                  <option value="custom">Custom range</option>
                </select>
              </div>
              
              <div>
                <label className="label">Report Title</label>
                <input
                  type="text"
                  className="input-field"
                  placeholder="Enter report title"
                  defaultValue={`OSINT Report - ${new Date().toLocaleDateString()}`}
                />
              </div>
              
              <div>
                <label className="label">Include Sections</label>
                <div className="space-y-2">
                  {[
                    'Executive Summary',
                    'Sentiment Analysis',
                    'Trend Analysis',
                    'Competitive Intelligence',
                    'Risk Assessment',
                    'Recommendations'
                  ].map((section) => (
                    <label key={section} className="flex items-center">
                      <input
                        type="checkbox"
                        defaultChecked
                        className="mr-2 rounded border-gray-300 focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700">{section}</span>
                    </label>
                  ))}
                </div>
              </div>
            </form>
            
            <div className="flex justify-end space-x-4 mt-6">
              <button
                onClick={() => setShowGenerateModal(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleGenerateReport}
                className="btn-primary"
              >
                Generate Report
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Reports;

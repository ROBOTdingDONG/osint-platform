/**
 * Data Sources Page for OSINT Platform
 * Manages data collection sources and configurations
 */

import React, { useState } from 'react';
import { useQuery } from 'react-query';
import {
  PlusIcon,
  Cog6ToothIcon,
  TrashIcon,
  PlayIcon,
  PauseIcon,
} from '@heroicons/react/24/outline';
import { api } from '../services/api';

const DataSources: React.FC = () => {
  const [showAddModal, setShowAddModal] = useState(false);

  // Fetch data sources
  const { data: sourcesData, isLoading } = useQuery(
    'dataSources',
    api.dataSources.list,
    {
      refetchInterval: 30000,
    }
  );

  const sources = sourcesData?.sources || [];

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
          <h1 className="text-3xl font-bold text-gray-900">Data Sources</h1>
          <p className="mt-2 text-gray-600">
            Manage your OSINT data collection sources and configurations.
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="btn-primary flex items-center"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          Add Source
        </button>
      </div>

      {/* Sources Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {sources.map((source) => (
          <div key={source.id} className="card hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <div className={`w-3 h-3 rounded-full mr-3 ${
                  source.status === 'active' ? 'bg-green-500' :
                  source.status === 'inactive' ? 'bg-gray-500' :
                  'bg-red-500'
                }`}></div>
                <h3 className="text-lg font-semibold text-gray-900">{source.name}</h3>
              </div>
              <div className="flex space-x-2">
                <button className="p-1 text-gray-400 hover:text-gray-600">
                  {source.status === 'active' ? (
                    <PauseIcon className="h-5 w-5" />
                  ) : (
                    <PlayIcon className="h-5 w-5" />
                  )}
                </button>
                <button className="p-1 text-gray-400 hover:text-gray-600">
                  <Cog6ToothIcon className="h-5 w-5" />
                </button>
                <button className="p-1 text-gray-400 hover:text-red-600">
                  <TrashIcon className="h-5 w-5" />
                </button>
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Type:</span>
                <span className="font-medium capitalize">{source.type}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Status:</span>
                <span className={`badge ${
                  source.status === 'active' ? 'success' :
                  source.status === 'inactive' ? 'info' :
                  'error'
                }`}>
                  {source.status}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Last Collection:</span>
                <span className="text-gray-500">2 hours ago</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Data Points:</span>
                <span className="font-medium">1,247</span>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-gray-200">
              <button className="w-full btn-secondary text-sm">
                View Details
              </button>
            </div>
          </div>
        ))}

        {/* Empty State */}
        {sources.length === 0 && (
          <div className="col-span-full">
            <div className="text-center py-12">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">
                No data sources
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by adding your first data source.
              </p>
              <div className="mt-6">
                <button
                  onClick={() => setShowAddModal(true)}
                  className="btn-primary"
                >
                  <PlusIcon className="h-5 w-5 mr-2" />
                  Add Data Source
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Add Source Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Add Data Source
            </h3>
            <p className="text-gray-600 mb-6">
              Choose a data source type to begin collecting OSINT data.
            </p>
            
            <div className="grid grid-cols-2 gap-4 mb-6">
              <button className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors">
                <div className="text-center">
                  <div className="w-8 h-8 bg-blue-600 rounded-lg mx-auto mb-2 flex items-center justify-center">
                    <span className="text-white font-bold text-sm">T</span>
                  </div>
                  <h4 className="font-medium text-gray-900">Twitter</h4>
                  <p className="text-xs text-gray-500">Social media monitoring</p>
                </div>
              </button>
              
              <button className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors">
                <div className="text-center">
                  <div className="w-8 h-8 bg-red-600 rounded-lg mx-auto mb-2 flex items-center justify-center">
                    <span className="text-white font-bold text-sm">N</span>
                  </div>
                  <h4 className="font-medium text-gray-900">News</h4>
                  <p className="text-xs text-gray-500">News and articles</p>
                </div>
              </button>
            </div>
            
            <div className="flex justify-end space-x-4">
              <button
                onClick={() => setShowAddModal(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button className="btn-primary">Continue</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DataSources;

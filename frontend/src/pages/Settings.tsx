/**
 * Settings Page for OSINT Platform
 * User preferences, account settings, and configuration
 */

import React, { useState } from 'react';
import {
  UserIcon,
  BellIcon,
  ShieldCheckIcon,
  KeyIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '../hooks/useAuth';

const Settings: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');
  
  const tabs = [
    { id: 'profile', name: 'Profile', icon: UserIcon },
    { id: 'notifications', name: 'Notifications', icon: BellIcon },
    { id: 'security', name: 'Security', icon: ShieldCheckIcon },
    { id: 'api', name: 'API Keys', icon: KeyIcon },
    { id: 'preferences', name: 'Preferences', icon: Cog6ToothIcon },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="mt-2 text-gray-600">
          Manage your account settings and preferences.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Settings Navigation */}
        <div className="lg:col-span-1">
          <nav className="space-y-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                  activeTab === tab.id
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <tab.icon className="h-5 w-5 mr-3" />
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Settings Content */}
        <div className="lg:col-span-3">
          {activeTab === 'profile' && (
            <div className="card">
              <div className="card-header">
                <h3 className="text-lg font-semibold text-gray-900">Profile Information</h3>
                <p className="text-sm text-gray-600">Update your account profile and email address</p>
              </div>
              
              <form className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="label">Full Name</label>
                    <input
                      type="text"
                      className="input-field"
                      defaultValue={user?.full_name}
                    />
                  </div>
                  <div>
                    <label className="label">Email Address</label>
                    <input
                      type="email"
                      className="input-field"
                      defaultValue={user?.email}
                    />
                  </div>
                </div>
                
                <div>
                  <label className="label">Company</label>
                  <input
                    type="text"
                    className="input-field"
                    defaultValue={user?.company || ''}
                    placeholder="Enter your company name"
                  />
                </div>
                
                <div>
                  <label className="label">Timezone</label>
                  <select className="input-field">
                    <option value="UTC">UTC</option>
                    <option value="America/New_York">Eastern Time</option>
                    <option value="America/Los_Angeles">Pacific Time</option>
                    <option value="Europe/London">London</option>
                  </select>
                </div>
                
                <div className="flex justify-end">
                  <button type="submit" className="btn-primary">
                    Save Changes
                  </button>
                </div>
              </form>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="card">
              <div className="card-header">
                <h3 className="text-lg font-semibold text-gray-900">Notification Preferences</h3>
                <p className="text-sm text-gray-600">Choose how you want to be notified</p>
              </div>
              
              <div className="space-y-6">
                {[
                  { id: 'email_alerts', label: 'Email Alerts', description: 'Receive alerts via email' },
                  { id: 'data_collection', label: 'Data Collection Updates', description: 'Notifications about data collection status' },
                  { id: 'analysis_complete', label: 'Analysis Complete', description: 'When analysis jobs finish' },
                  { id: 'report_ready', label: 'Report Ready', description: 'When reports are generated' },
                  { id: 'security_alerts', label: 'Security Alerts', description: 'Important security notifications' },
                ].map((setting) => (
                  <div key={setting.id} className="flex items-start">
                    <div className="flex h-5 items-center">
                      <input
                        id={setting.id}
                        type="checkbox"
                        defaultChecked
                        className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                    </div>
                    <div className="ml-3">
                      <label htmlFor={setting.id} className="text-sm font-medium text-gray-700">
                        {setting.label}
                      </label>
                      <p className="text-sm text-gray-500">{setting.description}</p>
                    </div>
                  </div>
                ))}
                
                <div className="flex justify-end">
                  <button className="btn-primary">
                    Save Preferences
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="space-y-6">
              <div className="card">
                <div className="card-header">
                  <h3 className="text-lg font-semibold text-gray-900">Change Password</h3>
                  <p className="text-sm text-gray-600">Update your account password</p>
                </div>
                
                <form className="space-y-4">
                  <div>
                    <label className="label">Current Password</label>
                    <input type="password" className="input-field" />
                  </div>
                  <div>
                    <label className="label">New Password</label>
                    <input type="password" className="input-field" />
                  </div>
                  <div>
                    <label className="label">Confirm New Password</label>
                    <input type="password" className="input-field" />
                  </div>
                  
                  <div className="flex justify-end">
                    <button type="submit" className="btn-primary">
                      Update Password
                    </button>
                  </div>
                </form>
              </div>
              
              <div className="card">
                <div className="card-header">
                  <h3 className="text-lg font-semibold text-gray-900">Two-Factor Authentication</h3>
                  <p className="text-sm text-gray-600">Add an extra layer of security</p>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-700">Two-factor authentication</p>
                    <p className="text-sm text-gray-500">Not enabled</p>
                  </div>
                  <button className="btn-primary">
                    Enable 2FA
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'api' && (
            <div className="card">
              <div className="card-header">
                <h3 className="text-lg font-semibold text-gray-900">API Keys</h3>
                <p className="text-sm text-gray-600">Manage your API keys for external integrations</p>
              </div>
              
              <div className="space-y-4">
                <div className="flex justify-end">
                  <button className="btn-primary">
                    Generate New Key
                  </button>
                </div>
                
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-700">Production Key</p>
                      <p className="text-sm text-gray-500">Created on January 15, 2024</p>
                      <p className="text-xs text-gray-400 font-mono">osint_key_prod_****7x9z</p>
                    </div>
                    <div className="flex space-x-2">
                      <button className="btn-secondary text-sm">
                        Regenerate
                      </button>
                      <button className="btn-danger text-sm">
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'preferences' && (
            <div className="card">
              <div className="card-header">
                <h3 className="text-lg font-semibold text-gray-900">Platform Preferences</h3>
                <p className="text-sm text-gray-600">Customize your OSINT platform experience</p>
              </div>
              
              <div className="space-y-6">
                <div>
                  <label className="label">Default Dashboard View</label>
                  <select className="input-field">
                    <option value="overview">Overview</option>
                    <option value="detailed">Detailed Metrics</option>
                    <option value="custom">Custom Layout</option>
                  </select>
                </div>
                
                <div>
                  <label className="label">Data Refresh Interval</label>
                  <select className="input-field">
                    <option value="30">30 seconds</option>
                    <option value="60">1 minute</option>
                    <option value="300">5 minutes</option>
                    <option value="900">15 minutes</option>
                  </select>
                </div>
                
                <div>
                  <label className="label">Export Format Preference</label>
                  <select className="input-field">
                    <option value="pdf">PDF</option>
                    <option value="excel">Excel</option>
                    <option value="csv">CSV</option>
                    <option value="json">JSON</option>
                  </select>
                </div>
                
                <div className="flex justify-end">
                  <button className="btn-primary">
                    Save Preferences
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Settings;

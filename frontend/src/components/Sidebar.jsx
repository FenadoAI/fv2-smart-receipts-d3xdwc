import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Home, 
  Upload, 
  Receipt, 
  BarChart3, 
  Settings, 
  Zap,
  FileText,
  TrendingUp 
} from 'lucide-react';

const Sidebar = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: Home },
    { path: '/upload', label: 'Upload Receipt', icon: Upload },
    { path: '/receipts', label: 'All Receipts', icon: Receipt },
    { path: '/analytics', label: 'Analytics', icon: BarChart3 },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <div className="w-64 bg-white shadow-lg h-full flex flex-col">
      {/* Logo/Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="bg-blue-600 p-2 rounded-lg">
            <Zap className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Receiptor AI</h1>
            <p className="text-sm text-gray-500">Smart Receipt Management</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <div className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors duration-200 ${
                  isActive(item.path)
                    ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                <Icon className={`h-5 w-5 ${isActive(item.path) ? 'text-blue-700' : 'text-gray-400'}`} />
                <span className="font-medium">{item.label}</span>
              </Link>
            );
          })}
        </div>

        {/* Quick Stats */}
        <div className="mt-8 p-4 bg-gray-50 rounded-lg">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Quick Stats</h3>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">This Month</span>
              <span className="font-semibold text-gray-900">24 receipts</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Total Spent</span>
              <span className="font-semibold text-green-600">$1,847.50</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Auto-categorized</span>
              <span className="font-semibold text-blue-600">96%</span>
            </div>
          </div>
        </div>

        {/* Upgrade Banner */}
        <div className="mt-6 p-4 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg text-white">
          <div className="flex items-center space-x-2 mb-2">
            <TrendingUp className="h-4 w-4" />
            <span className="text-sm font-semibold">Upgrade to Pro</span>
          </div>
          <p className="text-xs text-blue-100 mb-3">
            Unlimited receipts, advanced AI rules, and Xero/QBO sync
          </p>
          <button className="w-full bg-white text-blue-600 text-xs font-semibold py-2 px-3 rounded hover:bg-blue-50 transition-colors duration-200">
            Upgrade Now
          </button>
        </div>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
            <span className="text-sm font-semibold text-gray-600">JD</span>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-900">John Doe</p>
            <p className="text-xs text-gray-500">john@example.com</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;